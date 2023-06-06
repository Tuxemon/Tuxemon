# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, Sequence, Tuple

import pygame_menu

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.session import local_session
from tuxemon.states.journal import MonsterInfoState
from tuxemon.states.techniques import TechniqueMenuState
from tuxemon.tools import open_choice_dialog, open_dialog

if TYPE_CHECKING:
    from tuxemon.monster import Monster

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

        # Main Menu - Allows users to open the main menu in game.
        menu_items_map = [
            ("menu_monster", self.open_monster_menu),
            ("menu_bag", change_state("ItemMenuState")),
            ("menu_player", change_state("PlayerState")),
            ("menu_save", change_state("SaveMenuState")),
            ("menu_load", change_state("LoadMenuState")),
            ("menu_options", change_state("ControlState")),
            ("exit", exit_game),
        ]
        if local_session.player.find_item("nu_phone"):
            menu_items_map.insert(3, ("nu_phone", change_state("NuPhone")))
        if local_session.player.find_item("app_tuxepedia"):
            menu_items_map.insert(
                0,
                ("menu_tuxepedia", change_state("JournalChoice")),
            )
        add_menu_items(self.menu, tuple(menu_items_map))

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
                original = monster_menu.get_selected_item()
                if original:
                    original_monster = original.game_object
                    assert original_monster
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

        def select_first_monster(monster: Monster) -> None:
            # TODO: API for getting the game player obj
            player = local_session.player
            context["monster"] = monster
            context["old_index"] = player.monsters.index(monster)
            self.client.pop_state()  # close the info/move menu

        def open_monster_stats(monster: Monster) -> None:
            """Show monster statistics."""
            self.client.pop_state()
            self.client.push_state(MonsterInfoState(monster=monster))

        def positive_answer(monster: Monster) -> None:
            success = False
            player = local_session.player
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

        def release_monster_from_party(monster: Monster) -> None:
            """Show release monster confirmation dialog."""
            # Remove the submenu and replace with a confirmation dialog
            self.client.pop_state()
            open_dialog(
                local_session,
                [T.format("release_confirmation", {"name": monster.name})],
            )
            open_choice_dialog(
                local_session,
                menu=(
                    ("no", T.translate("no"), negative_answer),
                    (
                        "yes",
                        T.translate("yes"),
                        partial(positive_answer, monster),
                    ),
                ),
                escape_key_exits=False,
            )

        def open_monster_techs(monster: Monster) -> None:
            """Show techniques."""
            self.client.pop_state()
            self.client.push_state(TechniqueMenuState(monster=monster))

        def open_monster_submenu(
            menu_item: MenuItem[WorldMenuGameObj],
        ) -> None:
            original = monster_menu.get_selected_item()
            if original:
                monster = original.game_object
                if monster:
                    open_choice_dialog(
                        local_session,
                        menu=(
                            (
                                "info",
                                T.translate("monster_menu_info").upper(),
                                partial(open_monster_stats, monster),
                            ),
                            (
                                "tech",
                                T.translate("monster_menu_tech").upper(),
                                partial(open_monster_techs, monster),
                            ),
                            (
                                "move",
                                T.translate("monster_menu_move").upper(),
                                partial(select_first_monster, monster),
                            ),
                            (
                                "release",
                                T.translate("monster_menu_release").upper(),
                                partial(release_monster_from_party, monster),
                            ),
                        ),
                        escape_key_exits=True,
                    )

        def handle_selection(menu_item: MenuItem[WorldMenuGameObj]) -> None:
            if "monster" in context:
                del context["monster"]
            else:
                open_monster_submenu(menu_item)

        context: Dict[
            str, Any
        ] = dict()  # dict passed around to hold info between menus/callbacks
        monster_menu = self.client.push_state(MonsterMenuState())
        monster_menu.on_menu_selection = handle_selection  # type: ignore[assignment]
        monster_menu.on_menu_selection_change = monster_menu_hook  # type: ignore[method-assign]

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
