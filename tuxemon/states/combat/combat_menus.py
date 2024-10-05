# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING

import pygame
from pygame.rect import Rect

from tuxemon import combat, graphics, tools
from tuxemon.db import ElementType, State, TechSort
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
        common_menu_items = (
            ("menu_fight", self.open_technique_menu, True),
            ("menu_monster", self.open_swap_menu, True),
            ("menu_item", self.open_item_menu, True),
        )

        if self.combat.is_trainer_battle:
            menu_items_map = common_menu_items + (
                ("menu_forfeit", self.forfeit, self.enemy.forfeit),
            )
        else:
            menu_items_map = common_menu_items + (
                ("menu_run", self.run, True),
            )

        for key, callback, enable in menu_items_map:
            foreground = self.unavailable_color if not enable else None
            yield MenuItem(
                self.shadow_text(T.translate(key).upper(), fg=foreground),
                T.translate(key).upper(),
                None,
                callback,
                enable,
            )

    def forfeit(self) -> None:
        """
        Cause player to forfeit from the trainer battles.

        """
        forfeit = Technique()
        forfeit.load("menu_forfeit")
        forfeit.combat_state = self.combat
        self.client.pop_state(self)
        self.combat.enqueue_action(self.party[0], forfeit, self.opponents[0])

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
        self.combat.enqueue_action(self.party[0], run, self.opponents[0])

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
                if item.behaviors.throwable:
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
            if not item.behaviors.throwable:
                self.client.pop_state()  # close the monster action menu

        choose_item()

    def open_technique_menu(self) -> None:
        """Open menus to choose a Technique to use."""

        def choose_technique() -> None:
            available_techniques = [
                tech
                for tech in self.monster.moves
                if not combat.recharging(tech)
            ]

            # open menu to choose technique
            menu = self.client.push_state(Menu())
            menu.shrink_to_items = True

            if not available_techniques:
                skip = Technique()
                skip.load("skip")
                skip_image = self.shadow_text(skip.name)
                tech_skip = MenuItem(skip_image, None, None, skip)
                menu.add(tech_skip)

            for tech in self.monster.moves:
                tech_name = tech.name
                tech_color = None
                tech_enabled = True

                if combat.recharging(tech):
                    tech_name = f"{tech.name} ({abs(tech.next_use)})"
                    tech_color = self.unavailable_color
                    tech_enabled = False

                tech_image = self.shadow_text(tech_name, fg=tech_color)
                item = MenuItem(tech_image, None, None, tech, tech_enabled)
                menu.add(item)

            # Update selected_index to the first enabled item
            enabled_items = [
                i for i, item in enumerate(menu.menu_items) if item.enabled
            ]
            if enabled_items:
                menu.selected_index = enabled_items[0]

            # position the new menu
            menu.anchor("bottom", self.rect.top)
            menu.anchor("right", self.client.screen.get_rect().right)

            # set next menu after the selection is made
            menu.on_menu_selection = choose_target  # type: ignore[assignment]

        def choose_target(menu_item: MenuItem[Technique]) -> None:
            # open menu to choose target of technique
            technique = menu_item.game_object

            # allow to choose target if 1 vs 2 or 2 vs 2
            if len(self.opponents) > 1:
                state = self.client.push_state(
                    CombatTargetMenuState(
                        combat_state=self.combat,
                        monster=self.monster,
                        technique=technique,
                    )
                )
                state.on_menu_selection = partial(enqueue_technique, technique)  # type: ignore[method-assign]
            else:
                player = self.party[0]
                enemy = self.opponents[0]
                surface = pygame.Surface(self.rect.size)
                if technique.target["own_monster"]:
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

            # Check if the technique can be used on the target
            if not technique.validate(target):
                params = {"name": technique.name.upper()}
                msg = T.format("cannot_use_tech_monster", params)
                tools.open_dialog(local_session, [msg])
                return

            if (
                combat.has_effect(technique, "damage")
                and target == self.monster
            ):
                params = {"name": technique.name.upper()}
                msg = T.format("combat_target_itself", params)
                tools.open_dialog(local_session, [msg])
                return

            # Pre-check the technique for validity
            self.character.game_variables["action_tech"] = technique.slug
            technique = combat.pre_checking(
                self.monster, technique, target, self.combat
            )

            # Enqueue the action
            self.combat.enqueue_action(self.monster, technique, target)

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
        combat_state: CombatState,
        monster: Monster,
        technique: Technique,
    ) -> None:
        """
        Initializes the CombatTargetMenuState.

        Parameters:
            combat_state: The current combat state.
            monster: The monster that is using the technique.
            technique: The technique being used.
        """
        super().__init__()
        assert monster.owner
        self.monster = monster
        self.combat_state = combat_state
        self.character = monster.owner
        self.technique = technique
        self.party = combat_state.monsters_in_play[self.character]
        self._determine_enemy_and_opponents()
        self._create_menu()

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        self.targeting_map: defaultdict[str, list[Monster]] = defaultdict(list)

        if (
            self.technique.has_type(ElementType.aether)
            or self.technique.sort == TechSort.meta
        ):
            sprite = self.combat_state._monster_sprite_map[self.monster]
            aet = MenuItem(self.surface, None, self.monster.name, self.monster)
            aet.rect = sprite.rect.copy()
            aet.rect.inflate_ip(tools.scale(8), tools.scale(8))
            yield aet
            return

        for player, monsters in self.combat_state.monsters_in_play.items():
            if len(monsters) == 2:
                targeting_class = (
                    "own_monster"
                    if player == self.character
                    else "enemy_monster"
                )
                self.targeting_map[targeting_class].extend(monsters)

                if (
                    targeting_class not in self.technique.target
                    or not self.technique.target[targeting_class]
                ):
                    continue

                for monster in monsters:
                    sprite = self.combat_state._monster_sprite_map[monster]
                    mon = MenuItem(self.surface, None, monster.name, monster)
                    mon.rect = sprite.rect.copy()
                    mon.rect.inflate_ip(tools.scale(8), tools.scale(8))
                    if monster == monsters[0]:
                        mon.rect.right = sprite.rect.right
                    else:
                        mon.rect.left = sprite.rect.left
                    yield mon

    def _determine_enemy_and_opponents(self) -> None:
        """
        Determines the enemy and opponents based on the character.
        """
        if self.character == self.combat_state.players[0]:
            self.enemy = self.combat_state.players[1]
            self.opponents = self.combat_state.monsters_in_play[self.enemy]
        elif self.character == self.combat_state.players[1]:
            self.enemy = self.combat_state.players[0]
            self.opponents = self.combat_state.monsters_in_play[self.enemy]

    def _create_menu(self) -> None:
        """
        Creates the menu.
        """
        rect_screen = self.client.screen.get_rect()
        menu_width = rect_screen.w // 2
        menu_height = rect_screen.h // 4
        rect = Rect(0, 0, menu_width, menu_height)
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

    def determine_target(self) -> None:
        """
        Determines the optimal target.
        """
        for target_tag, target_value in self.technique.target.items():
            if target_value:
                for target in self.targeting_map.get(target_tag, []):
                    menu_item = self.search_items(target)
                    if menu_item and menu_item.enabled:
                        self._set_selected_index(menu_item)

    def _set_selected_index(self, menu_item: MenuItem[Monster]) -> None:
        """
        Sets the selected index to the index of the given menu item.
        """
        try:
            index = self.menu_items.sprites().index(menu_item)
            self.selected_index = index
        except ValueError:
            # Handle the case where menu_item is not found in self.menu_items
            raise ValueError(f"Menu item {menu_item} not found in menu items")

    def refresh_layout(self) -> None:
        """
        Refreshes the layout after determining the optimal target.
        """
        self.determine_target()
        super().refresh_layout()

    def _clear_old_borders(self) -> None:
        """
        Clears out the old borders.
        """
        for sprite in self.menu_items:
            sprite.image.fill((0, 0, 0, 0))
            sprite.remove()

    def _draw_new_border(self) -> None:
        """
        Draws a new border around the selected item.
        """
        selected_item = self.get_selected_item()
        if selected_item:
            selected_item.image = pygame.Surface(
                selected_item.rect.size, pygame.SRCALPHA
            )
            self.border.draw(selected_item.image)

            # Show item description
            if selected_item.description:
                self.alert(selected_item.description)

    def on_menu_selection_change(self) -> None:
        """
        Draws borders around sprites when selection changes.
        """
        self._clear_old_borders()
        self._draw_new_border()
