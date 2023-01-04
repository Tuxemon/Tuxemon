# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from functools import partial
from typing import Any, Callable, Dict, Sequence, Tuple

import pygame_menu

from tuxemon import formula, prepare
from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.session import local_session
from tuxemon.states.choice import ChoiceState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


WorldMenuGameObj = Callable[[], object]


def add_menu_items(
    menu: pygame_menu.Menu,
    items: Sequence[Tuple[str, WorldMenuGameObj]],
) -> None:

    menu.add.vertical_fill()
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)
        menu.add.vertical_fill()

    width, height = prepare.SCREEN_SIZE
    widgets_size = menu.get_size(widget=True)
    b_width, b_height = menu.get_scrollarea().get_border_size()
    menu.resize(
        widgets_size[0],
        height - 2 * b_height,
        position=(width + b_width, b_height, False),
    )


class WorldMenuState(PygameMenuState):
    """Menu for the world state."""

    def __init__(self) -> None:
        _, height = prepare.SCREEN_SIZE

        super().__init__(height=height)

        self.animation_offset = 0

        def change_state(state: str, **kwargs: Any) -> Callable[[], object]:
            return partial(self.client.replace_state, state, **kwargs)

        def exit_game() -> None:
            self.client.event_engine.execute_action("quit")

        def not_implemented_dialog() -> None:
            open_dialog(local_session, [T.translate("not_implemented")])

        # Main Menu - Allows users to open the main menu in game.
        menu_items_map = (
            ("menu_journal", not_implemented_dialog),
            ("menu_monster", self.open_monster_menu),
            ("menu_bag", change_state("ItemMenuState")),
            ("menu_player", not_implemented_dialog),
            ("menu_save", change_state("SaveMenuState")),
            ("menu_load", change_state("LoadMenuState")),
            ("menu_options", change_state("ControlState")),
            ("exit", exit_game),
        )
        add_menu_items(self.menu, menu_items_map)

    def open_monster_menu(self) -> None:
        from tuxemon.states.monster import MonsterMenuState

        def monster_menu_hook() -> None:
            """
            Used to rearrange monsters interactively.

            This is slow b/c forces each slot to be re-rendered.
            Probably not an issue except for very slow systems.

            """
            monster = context.get("monster")
            if monster:
                # TODO: maybe some API for re-arranging menu items
                # at this point, the cursor will have changed
                # so we need to re-arrange the list before it is rendered again
                # TODO: API for getting the game player object
                player = local_session.player
                monster_list = player.monsters

                # get the newly selected item.  it will be set to previous
                # position
                original_monster = monster_menu.get_selected_item().game_object

                # get the position in the list of the cursor
                index = monster_list.index(original_monster)

                # set the old spot to the old monster
                monster_list[context["old_index"]] = original_monster

                # set the current cursor position to the monster we move
                monster_list[index] = context["monster"]

                # store the old index
                context["old_index"] = index

            # call the super class to re-render the menu with new positions
            # TODO: maybe add more hooks to eliminate this runtime patching
            MonsterMenuState.on_menu_selection_change(monster_menu)

        def select_first_monster() -> None:
            # TODO: API for getting the game player obj
            player = local_session.player
            monster = monster_menu.get_selected_item().game_object
            context["monster"] = monster
            context["old_index"] = player.monsters.index(monster)
            self.client.pop_state()  # close the info/move menu

        def open_monster_stats() -> None:
            monster = monster_menu.get_selected_item().game_object
            type2 = ""
            if prepare.CONFIG.unit == "metric":
                weight = monster.weight
                height = monster.height
                unit_weight = "kg"
                unit_height = "cm"
            else:
                weight = formula.convert_lbs(monster.weight)
                height = formula.convert_ft(monster.height)
                unit_weight = "lb"
                unit_height = "ft"
            if monster.type2 is not None:
                type2 = monster.type2
            open_dialog(
                local_session,
                [
                    T.format(
                        "tuxemon_stat1",
                        {
                            "txmn": monster.txmn_id,
                            "doc": formula.today_ordinal() - monster.capture,
                            "weight": weight,
                            "height": height,
                            "unit_weight": unit_weight,
                            "unit_height": unit_height,
                            "lv": monster.level + 1,
                            "type": monster.type1.title() + type2.title(),
                            "exp": monster.total_experience,
                            "exp_lv": (
                                monster.experience_required(1)
                                - monster.total_experience
                            ),
                        },
                    ),
                    T.format(
                        "tuxemon_stat2",
                        {
                            "desc": monster.description,
                        },
                    ),
                ],
            )

        def positive_answer() -> None:
            success = False
            player = local_session.player
            monster = monster_menu.get_selected_item().game_object
            success = player.release_monster(monster)

            # Close the dialog and confirmation menu, and inform the user
            # their tuxemon has been released.
            if success:
                self.client.pop_state()
                self.client.pop_state()
                open_dialog(
                    local_session,
                    [T.format("tuxemon_released", {"name": monster.name})],
                )
                monster_menu.refresh_menu_items()
                monster_menu.on_menu_selection_change()
            else:
                open_dialog(local_session, [T.translate("cant_release")])

        def negative_answer() -> None:
            self.client.pop_state()  # close menu
            self.client.pop_state()  # close confirmation dialog

        def release_monster_from_party() -> None:
            """Show release monster confirmation dialog."""
            # Remove the submenu and replace with a confirmation dialog
            self.client.pop_state()

            monster = monster_menu.get_selected_item().game_object
            open_dialog(
                local_session,
                [T.format("release_confirmation", {"name": monster.name})],
            )
            self.client.push_state(
                ChoiceState(
                    menu=(
                        ("no", T.translate("no"), negative_answer),
                        ("yes", T.translate("yes"), positive_answer),
                    ),
                )
            )

        def open_monster_submenu(
            menu_item: MenuItem[WorldMenuGameObj],
        ) -> None:
            menu_items_map = (
                ("monster_menu_info", open_monster_stats),
                ("monster_menu_move", select_first_monster),
                ("monster_menu_release", release_monster_from_party),
            )
            menu = self.client.push_state(PygameMenuState())

            for key, callback in menu_items_map:
                label = T.translate(key).upper()
                menu.menu.add.button(label, callback)

            size = menu.menu.get_size(widget=True)
            menu.menu.resize(*size)

        def handle_selection(menu_item: MenuItem[WorldMenuGameObj]) -> None:
            if "monster" in context:
                del context["monster"]
            else:
                open_monster_submenu(menu_item)

        context: Dict[
            str, Any
        ] = dict()  # dict passed around to hold info between menus/callbacks
        monster_menu = self.client.replace_state(MonsterMenuState)
        monster_menu.on_menu_selection = handle_selection  # type: ignore[assignment]
        monster_menu.on_menu_selection_change = monster_menu_hook  # type: ignore[assignment]

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        """
        Animate the menu sliding in.

        Returns:
            Sliding in animation.

        """

        width = self.menu.get_width(border=True)
        self.animation_offset = 0

        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani

    def animate_close(self) -> Animation:
        """
        Animate the menu sliding out.

        Returns:
            Sliding out animation.

        """
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani
