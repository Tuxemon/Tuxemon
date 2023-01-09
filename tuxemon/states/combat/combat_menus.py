# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from functools import partial
from typing import TYPE_CHECKING, Callable, DefaultDict, Generator, List, Union

import pygame

from tuxemon import formula, graphics, tools
from tuxemon.combat import check_status
from tuxemon.db import ItemBattleMenu
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import MenuSpriteGroup, SpriteGroup
from tuxemon.state import State
from tuxemon.states.combat.combat import CombatState
from tuxemon.states.items import ItemMenuState
from tuxemon.states.monster import MonsterMenuState
from tuxemon.technique.technique import Technique
from tuxemon.ui.draw import GraphicBox

if TYPE_CHECKING:
    from tuxemon.player import NPC, Player

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

    def __init__(self, monster: Monster) -> None:
        super().__init__()

        self.monster = monster

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        combat_state = self.client.get_state_by_name(CombatState)
        if combat_state.is_trainer_battle:
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
        forfeit = Technique("menu_forfeit")
        if not forfeit.validate(self.monster):
            if check_status(self.monster, "status_grabbed") or check_status(
                self.monster, "status_stuck"
            ):
                tools.open_dialog(
                    local_session,
                    [
                        T.format(
                            "combat_player_forfeit_status",
                            {
                                "monster": self.monster.name,
                                "status": self.monster.status[0].name.lower(),
                            },
                        )
                    ],
                )
                return
        self.client.pop_state(self)
        combat_state = self.client.get_state_by_name(CombatState)
        # trigger forfeit
        for mon in combat_state.players[0].monsters:
            faint = Technique("status_faint")
            mon.current_hp = 0
            mon.status = [faint]

    def run(self) -> None:
        """
        Cause player to run from the wild encounters.

        TODO: only works for player0.

        """
        # TODO: only works for player0
        run = Technique("menu_run")
        if not run.validate(self.monster):
            if check_status(self.monster, "status_grabbed") or check_status(
                self.monster, "status_stuck"
            ):
                tools.open_dialog(
                    local_session,
                    [
                        T.format(
                            "combat_player_run_status",
                            {
                                "monster": self.monster.name,
                                "status": self.monster.status[0].name.lower(),
                            },
                        )
                    ],
                )
                return
        self.client.pop_state(self)
        combat_state = self.client.get_state_by_name(CombatState)
        player = combat_state.monsters_in_play[combat_state.players[0]][0]
        target = combat_state.monsters_in_play[combat_state.players[1]][0]
        var = combat_state.players[0].game_variables
        # if the variable doesn't exist
        if "run_attempts" not in var:
            var["run_attempts"] = 0
        if (
            formula.escape(player.level, target.level, var["run_attempts"])
            and combat_state._run == "on"
        ):
            var["run_attempts"] += 1
            # trigger run
            del combat_state.monsters_in_play[combat_state.players[0]]
            combat_state.players.remove(combat_state.players[0])
        else:

            def open_menu() -> None:
                combat_state.task(
                    partial(
                        combat_state.show_monster_action_menu,
                        self.monster,
                    ),
                    1,
                )

            combat_state.alert(
                T.translate("combat_can't_run_from_trainer"),
                open_menu,
            )
            combat_state._run = "off"

    def open_swap_menu(self) -> None:
        """Open menus to swap monsters in party."""

        def swap_it(menuitem: MenuItem[Monster]) -> None:
            monster = menuitem.game_object

            if (
                monster
                in self.client.get_state_by_name(CombatState).active_monsters
            ):
                tools.open_dialog(
                    local_session,
                    [T.format("combat_isactive", {"name": monster.name})],
                )
                return
            elif monster.current_hp < 1:
                tools.open_dialog(
                    local_session,
                    [T.format("combat_fainted", {"name": monster.name})],
                )
                return
            combat_state = self.client.get_state_by_name(CombatState)
            swap = Technique("swap")
            swap.combat_state = combat_state
            if not swap.validate(self.monster):
                if check_status(
                    self.monster, "status_grabbed"
                ) or check_status(self.monster, "status_stuck"):
                    tools.open_dialog(
                        local_session,
                        [
                            T.format(
                                "combat_player_swap_status",
                                {
                                    "monster": self.monster.name,
                                    "status": self.monster.status[
                                        0
                                    ].name.lower(),
                                },
                            )
                        ],
                    )
                    return
            player = local_session.player
            target = monster
            combat_state.enqueue_action(player, swap, target)
            self.client.pop_state()  # close technique menu
            self.client.pop_state()  # close the monster action menu

        menu = self.client.push_state(MonsterMenuState())
        menu.on_menu_selection = swap_it  # type: ignore[assignment]
        menu.anchor("bottom", self.rect.top)
        menu.anchor("right", self.client.screen.get_rect().right)
        menu.monster = self.monster

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""

        def choose_item() -> None:
            # open menu to choose item
            menu = self.client.push_state(ItemMenuState())

            # set next menu after after selection is made
            menu.on_menu_selection = choose_target  # type: ignore[assignment]

        def choose_target(menu_item: MenuItem[Item]) -> None:
            # open menu to choose target of item
            item = menu_item.game_object
            self.client.pop_state()  # close the item menu
            # TODO: don't hardcode to player0
            combat_state = self.client.get_state_by_name(CombatState)

            state: State
            if item.battle_menu == ItemBattleMenu.monster:
                state = self.client.push_state(MonsterMenuState())
                state.on_menu_selection = partial(enqueue_item, item)  # type: ignore[assignment]
            else:
                state = self.client.push_state(
                    CombatTargetMenuState(
                        player=combat_state.players[0],
                        user=combat_state.players[0],
                        action=item,
                    )
                )
                state.on_menu_selection = partial(enqueue_item, item)  # type: ignore[assignment]

        def enqueue_item(item: Item, menu_item: MenuItem[Monster]) -> None:
            target = menu_item.game_object
            # is the item valid to use?
            if not item.validate(target):
                msg = T.format("cannot_use_item_monster", {"name": item.name})
                tools.open_dialog(local_session, [msg])
                return

            # enqueue the item
            combat_state = self.client.get_state_by_name(CombatState)
            # TODO: don't hardcode to player0
            combat_state.enqueue_action(combat_state.players[0], item, target)

            # close all the open menus
            self.client.pop_state()  # close target chooser
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
                if tech.next_use <= 0:
                    image = self.shadow_text(tech.name)
                else:
                    image = self.shadow_text(
                        "%s %d" % (tech.name, abs(tech.next_use)),
                        fg=self.unavailable_color,
                    )
                    filter_moves.append(tech)
                # add skip move if both grey
                if len(filter_moves) == len(self.monster.moves):
                    skip = Technique("skip")
                    self.monster.moves.append(skip)
                item = MenuItem(image, None, None, tech)
                menu.add(item)

            # position the new menu
            menu.anchor("bottom", self.rect.top)
            menu.anchor("right", self.client.screen.get_rect().right)

            # set next menu after after selection is made
            menu.on_menu_selection = choose_target  # type: ignore[assignment]

        def choose_target(menu_item: MenuItem[Technique]) -> None:
            # open menu to choose target of technique
            technique = menu_item.game_object
            if technique.next_use > 0:
                params = {"move": technique.name, "name": self.monster.name}
                tools.open_dialog(
                    local_session,
                    [T.format("combat_recharging", params)],
                )
                return

            combat_state = self.client.get_state_by_name(CombatState)
            state = self.client.push_state(
                CombatTargetMenuState(
                    player=combat_state.players[0],
                    user=self.monster,
                    action=technique,
                )
            )
            state.on_menu_selection = partial(enqueue_technique, technique)  # type: ignore[assignment]

        def enqueue_technique(
            technique: Technique,
            menu_item: MenuItem[Monster],
        ) -> None:
            # enqueue the technique
            target = menu_item.game_object

            # can be used the technique?
            if not technique.validate(target):
                msg = T.format(
                    "cannot_use_tech_monster", {"name": technique.name}
                )
                tools.open_dialog(local_session, [msg])
                return

            if "damage" in technique.effects and target == self.monster:
                params = {"name": self.monster.name}
                msg = T.format("combat_target_itself", params)
                tools.open_dialog(local_session, [msg])
                return
            else:
                combat_state = self.client.get_state_by_name(CombatState)
                combat_state.enqueue_action(self.monster, technique, target)
                # remove skip after using it
                if technique.slug == "skip":
                    self.monster.moves.pop()

                # close all the open menus
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
        player: Player,
        user: Union[NPC, Monster],
        action: Union[Item, Technique],
    ) -> None:
        super().__init__()

        # used to determine how player can target techniques
        self.user = user
        self.action = action
        self.player = player

        # load and scale the menu borders
        border = graphics.load_and_scale(self.borders_filename)
        self.border = GraphicBox(border, None, None)

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        # get a ref to the combat state
        combat_state = self.client.get_state_by_name(CombatState)

        # TODO: trainer targeting
        # TODO: cleanup how monster sprites and whatnot are managed
        # TODO: This is going to work fine for simple matches, but controls
        # will be wonky for parties
        # TODO: (cont.) Need better handling of cursor keys for 2d layouts
        # of menu items get all the monster positions

        # this is used to determine who owns what monsters and what not
        # TODO: make less duplication of game data in memory, let combat
        # state have more registers, etc
        self.targeting_map: DefaultDict[str, List[Monster]] = defaultdict(list)

        for player, monsters in combat_state.monsters_in_play.items():
            for monster in monsters:

                # TODO: more targeting classes
                if player == self.player:
                    targeting_class = "own monster"
                else:
                    targeting_class = "enemy monster"

                self.targeting_map[targeting_class].append(monster)

                # TODO: handle odd cases where a situation creates no valid
                # targets if this target type is not handled by this action,
                # then skip it
                if targeting_class not in self.action.target:
                    continue

                # inspect the monster sprite and make a border image for it
                sprite = combat_state._monster_sprite_map[monster]
                item = MenuItem(None, None, None, monster)
                item.rect = sprite.rect.copy()
                center = item.rect.center
                item.rect.inflate_ip(tools.scale(16), tools.scale(16))
                item.rect.center = center

                yield item

    def refresh_layout(self) -> None:
        """Before refreshing the layout, determine the optimal target."""

        def determine_target() -> None:
            for tag in self.action.target:
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
            sprite.image = None

        # find the selected item and make a border for it
        item = self.get_selected_item()
        if item:
            item.image = pygame.Surface(item.rect.size, pygame.SRCALPHA)
            self.border.draw(item.image)
