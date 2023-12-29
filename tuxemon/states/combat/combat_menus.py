# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, DefaultDict

import pygame
from pygame.rect import Rect

from tuxemon import combat, graphics, tools
from tuxemon.db import ElementType, ItemCategory, State, TechSort
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import MenuSpriteGroup, SpriteGroup
from tuxemon.states.items.item_menu import ItemMenuState
from tuxemon.states.monster import MonsterMenuState
from tuxemon.technique.technique import Technique
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], None]


class MainCombatMenuState(PopUpMenu[MenuGameObj]):
    """
    Main menu for combat: Fight, Item, Swap, Run

    TODO: there needs to be more general use registers in the combat state to
    query what player is doing what. There's lots of spaghetti right now.
    """

    escape_key_exits = False
    columns = 2

    def __init__(self, cmb: CombatState, monster: Monster) -> None:
        super().__init__()
        assert monster.owner
        self.combat = cmb
        self.character = monster.owner
        self.monster = monster
        self.party = cmb.monsters_in_play[self.character]
        if self.character == cmb.players[0]:
            self.enemy = cmb.players[1]
            self.opponents = cmb.monsters_in_play[self.enemy]
        if self.character == cmb.players[1]:
            self.enemy = cmb.players[0]
            self.opponents = cmb.monsters_in_play[self.enemy]

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        if self.combat.is_trainer_battle:
            menu_items_map = (
                ("menu_fight", self.open_technique_menu),
                ("menu_monster", self.open_swap_menu),
                ("menu_item", self.open_item_menu),
                ("menu_forfeit", self.forfeit),
            )
        else:
            menu_items_map = (
                ("menu_fight", self.open_technique_menu),
                ("menu_monster", self.open_swap_menu),
                ("menu_item", self.open_item_menu),
                ("menu_run", self.run),
            )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            image = self.shadow_text(label)
            yield MenuItem(image, label, None, callback)

    def forfeit(self) -> None:
        """
        Cause player to forfeit from the trainer battles.

        """
        forfeit = Technique()
        forfeit.load("menu_forfeit")
        forfeit.combat_state = self.combat
        if not forfeit.validate(self.monster):
            params = {
                "monster": self.monster.name.upper(),
                "status": self.monster.status[0].name.lower(),
            }
            msg = T.format("combat_player_forfeit_status", params)
            tools.open_dialog(local_session, [msg])
            return
        self.client.pop_state(self)
        if not self.enemy.forfeit:

            def open_menu() -> None:
                self.combat.task(
                    partial(
                        self.combat.show_monster_action_menu,
                        self.monster,
                    ),
                    1,
                )

            self.combat.alert(
                T.translate("combat_forfeit_trainer"),
                open_menu,
            )
        else:
            player = self.party[0]
            enemy = self.opponents[0]
            self.combat.enqueue_action(player, forfeit, enemy)

    def run(self) -> None:
        """
        Cause player to run from the wild encounters.

        """
        run = Technique()
        run.load("menu_run")
        run.combat_state = self.combat
        if not run.validate(self.monster):
            params = {
                "monster": self.monster.name.upper(),
                "status": self.monster.status[0].name.lower(),
            }
            msg = T.format("combat_player_run_status", params)
            tools.open_dialog(local_session, [msg])
            return
        self.client.pop_state(self)
        player = self.party[0]
        enemy = self.opponents[0]
        self.combat.enqueue_action(player, run, enemy)

    def open_swap_menu(self) -> None:
        """Open menus to swap monsters in party."""

        def swap_it(menuitem: MenuItem[Monster]) -> None:
            added = menuitem.game_object

            if added in self.combat.active_monsters:
                msg = T.format("combat_isactive", {"name": added.name.upper()})
                tools.open_dialog(local_session, [msg])
                return
            if combat.fainted(added):
                msg = T.format("combat_fainted", {"name": added.name.upper()})
                tools.open_dialog(local_session, [msg])
                return
            swap = Technique()
            swap.load("swap")
            swap.combat_state = self.combat
            if not swap.validate(self.monster):
                params = {
                    "monster": self.monster.name.upper(),
                    "status": self.monster.status[0].name.lower(),
                }
                msg = T.format("combat_player_swap_status", params)
                tools.open_dialog(local_session, [msg])
                return
            self.combat.enqueue_action(self.monster, swap, added)
            self.client.pop_state()  # close technique menu
            self.client.pop_state()  # close the monster action menu

        menu = self.client.push_state(MonsterMenuState())
        menu.on_menu_selection = swap_it  # type: ignore[assignment]
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", self.client.screen.get_rect().right)

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""

        def choose_item() -> None:
            # open menu to choose item
            menu = self.client.push_state(ItemMenuState())

            # set next menu after the selection is made
            menu.on_menu_selection = choose_target  # type: ignore[method-assign]

        def choose_target(menu_item: MenuItem[Item]) -> None:
            # open menu to choose target of item
            item = menu_item.game_object
            self.client.pop_state()  # close the item menu
            if State["MainCombatMenuState"] in item.usable_in:
                if item.category == ItemCategory.capture:
                    enemy = self.opponents[0]
                    surface = pygame.Surface(self.rect.size)
                    mon = MenuItem(surface, None, None, enemy)
                    enqueue_item(item, mon)
                else:
                    state = self.client.push_state(MonsterMenuState())
                    state.on_menu_selection = partial(enqueue_item, item)  # type: ignore[method-assign]

        def enqueue_item(item: Item, menu_item: MenuItem[Monster]) -> None:
            target = menu_item.game_object
            # is the item valid to use?
            if not item.validate(target):
                params = {"name": item.name.upper()}
                msg = T.format("cannot_use_item_monster", params)
                tools.open_dialog(local_session, [msg])
                return
            # check target status
            if target.status:
                target.status[0].combat_state = self.combat
                target.status[0].phase = "enqueue_item"
                result_status = target.status[0].use(target)
                if result_status["extra"]:
                    tools.open_dialog(local_session, [result_status["extra"]])
                    return

            # enqueue the item
            self.combat.enqueue_action(self.character, item, target)

            # close all the open menus
            self.client.pop_state()  # close target chooser
            if item.category != ItemCategory.capture:
                self.client.pop_state()  # close the monster action menu

        choose_item()

    def open_technique_menu(self) -> None:
        """Open menus to choose a Technique to use."""

        def choose_technique() -> None:
            # open menu to choose technique
            menu = self.client.push_state(Menu())
            menu.shrink_to_items = True

            # add techniques to the menu
            filter_moves = []
            for tech in self.monster.moves:
                if not combat.recharging(tech):
                    image = self.shadow_text(tech.name)
                else:
                    image = self.shadow_text(
                        "%s %d" % (tech.name, abs(tech.next_use)),
                        fg=self.unavailable_color,
                    )
                    filter_moves.append(tech)
                # add skip move if both grey
                if len(filter_moves) == len(self.monster.moves):
                    skip = Technique()
                    skip.load("skip")
                    self.monster.moves.append(skip)
                item = MenuItem(image, None, None, tech)
                menu.add(item)

            # position the new menu
            menu.anchor("bottom", self.rect.top)
            menu.anchor("right", self.client.screen.get_rect().right)

            # set next menu after the selection is made
            menu.on_menu_selection = choose_target  # type: ignore[assignment]

        def choose_target(menu_item: MenuItem[Technique]) -> None:
            # open menu to choose target of technique
            technique = menu_item.game_object
            if combat.recharging(technique):
                params = {
                    "move": technique.name.upper(),
                    "name": self.monster.name.upper(),
                }
                msg = T.format("combat_recharging", params)
                tools.open_dialog(local_session, [msg])
                return

            # allow to choose target if 1 vs 2 or 2 vs 2
            if len(self.opponents) > 1:
                state = self.client.push_state(
                    CombatTargetMenuState(
                        cmb=self.combat,
                        monster=self.monster,
                        tech=technique,
                    )
                )
                state.on_menu_selection = partial(enqueue_technique, technique)  # type: ignore[method-assign]
            else:
                player = self.party[0]
                enemy = self.opponents[0]
                surface = pygame.Surface(self.rect.size)
                if "own monster" in technique.target:
                    mon = MenuItem(surface, None, None, player)
                else:
                    mon = MenuItem(surface, None, None, enemy)
                enqueue_technique(technique, mon)

        def enqueue_technique(
            technique: Technique,
            menu_item: MenuItem[Monster],
        ) -> None:
            # enqueue the technique
            target = menu_item.game_object

            params = {"name": self.monster.name.upper()}
            # can be used the technique?
            if not technique.validate(target):
                msg = T.format("cannot_use_tech_monster", params)
                tools.open_dialog(local_session, [msg])
                return

            if (
                combat.has_effect(technique, "damage")
                and target == self.monster
            ):
                msg = T.format("combat_target_itself", params)
                tools.open_dialog(local_session, [msg])
                return
            else:
                self.character.game_variables["action_tech"] = technique.slug
                # pre checking (look for null actions)
                technique = combat.pre_checking(
                    self.monster, technique, target, self.combat
                )
                self.combat.enqueue_action(self.monster, technique, target)
                # remove skip after using it
                if technique.slug == "skip":
                    self.monster.moves.pop()

                # close all the open menus
                if len(self.opponents) > 1:
                    self.client.pop_state()  # close target chooser
                self.client.pop_state()  # close technique menu
                self.client.pop_state()  # close the monster action menu

        choose_technique()


class CombatTargetMenuState(Menu[Monster]):
    """
    Menu for selecting targets of techniques and items.

    This special menu draws over the combat screen.

    """

    transparent = True

    def create_new_menu_items_group(self) -> None:
        # these groups will not automatically position the sprites
        self.menu_items = MenuSpriteGroup()
        self.menu_sprites = SpriteGroup()

    def __init__(
        self,
        cmb: CombatState,
        monster: Monster,
        tech: Technique,
    ) -> None:
        super().__init__()
        assert monster.owner
        self.monster = monster
        self.combat = cmb
        self.character = monster.owner
        self.monster = monster
        self.tech = tech
        self.party = cmb.monsters_in_play[self.character]
        if self.character == cmb.players[0]:
            self.enemy = cmb.players[1]
            self.opponents = cmb.monsters_in_play[self.enemy]
        if self.character == cmb.players[1]:
            self.enemy = cmb.players[0]
            self.opponents = cmb.monsters_in_play[self.enemy]

        # creates menu
        rect_screen = self.client.screen.get_rect()
        rect = Rect(0, 0, rect_screen.w // 2, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h
        border = graphics.load_and_scale(self.borders_filename)
        self.dialog_box = GraphicBox(border, None, self.background_color)
        self.dialog_box.rect = rect
        self.sprites.add(self.dialog_box, layer=100)
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.dialog_box.calc_inner_rect(
            self.dialog_box.rect,
        )
        self.sprites.add(self.text_area, layer=100)

        # load and scale the menu borders
        border = graphics.load_and_scale(self.borders_filename)
        self.border = GraphicBox(border, None, None)

        rect = Rect((0, 0), self.rect.size)
        self.surface = pygame.Surface(rect.size, pygame.SRCALPHA)

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        # TODO: trainer targeting
        # TODO: cleanup how monster sprites and whatnot are managed
        # TODO: This is going to work fine for simple matches, but controls
        # will be wonky for parties
        # TODO: (cont.) Need better handling of cursor keys for 2d layouts
        # of menu items get all the monster positions

        # this is used to determine who owns what monsters and what not
        # TODO: make less duplication of game data in memory, let combat
        # state have more registers, etc
        self.targeting_map: DefaultDict[str, list[Monster]] = defaultdict(list)
        # avoid choosing multiple targets (aether type tech)
        if (
            self.tech.has_type(ElementType.aether)
            or self.tech.sort == TechSort.meta
        ):
            sprite = self.combat._monster_sprite_map[self.monster]
            aet = MenuItem(self.surface, None, self.monster.name, self.monster)
            aet.rect = sprite.rect.copy()
            aet.rect.inflate_ip(tools.scale(8), tools.scale(8))
            yield aet
            return

        for player, monsters in self.combat.monsters_in_play.items():
            if len(monsters) == 2:
                for monster in monsters:
                    # allow choosing multiple targets
                    if player == self.character:
                        targeting_class = "own monster"
                    else:
                        targeting_class = "enemy monster"

                    self.targeting_map[targeting_class].append(monster)

                    # TODO: handle odd cases where a situation creates no valid
                    # targets if this target type is not handled by this action,
                    # then skip it
                    if targeting_class not in self.tech.target:
                        continue

                    # inspect the monster sprite and make a border image for it
                    sprite = self.combat._monster_sprite_map[monster]
                    mon1 = MenuItem(
                        self.surface, None, monsters[0].name, monsters[0]
                    )
                    mon1.rect = sprite.rect.copy()
                    right = mon1.rect.right
                    mon1.rect.inflate_ip(tools.scale(8), tools.scale(8))
                    mon1.rect.right = right
                    yield mon1
                    mon2 = MenuItem(
                        self.surface, None, monsters[1].name, monsters[1]
                    )
                    mon2.rect = sprite.rect.copy()
                    left = mon2.rect.left
                    mon2.rect.inflate_ip(tools.scale(8), tools.scale(8))
                    mon2.rect.left = left
                    yield mon2

    def refresh_layout(self) -> None:
        """Before refreshing the layout, determine the optimal target."""

        def determine_target() -> None:
            for tag in self.tech.target:
                for target in self.targeting_map[tag]:
                    menu_item = self.search_items(target)
                    assert menu_item
                    if menu_item.enabled:
                        # TODO: some API for this mess
                        # get the index of the menu_item
                        # change it
                        index = self.menu_items.sprites().index(menu_item)
                        self.selected_index = index
                        return

        determine_target()
        super().refresh_layout()

    def on_menu_selection_change(self) -> None:
        """Draw borders around sprites when selection changes."""
        # clear out the old borders
        for sprite in self.menu_items:
            sprite.remove()

        # find the selected item and make a border for it
        item = self.get_selected_item()
        if item:
            item.image = pygame.Surface(item.rect.size, pygame.SRCALPHA)
            self.border.draw(item.image)

            # show item description
            if item.description:
                self.alert(item.description)
