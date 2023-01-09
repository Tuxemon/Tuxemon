# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Start state.
"""
from __future__ import annotations

import logging
from functools import partial
from typing import Any, Callable, Tuple, Union

import pygame

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.save import get_index_of_latest_save
from tuxemon.session import local_session
from tuxemon.state import State
from tuxemon.states.transition.fade import FadeInTransition

logger = logging.getLogger(__name__)

StartGameObj = Callable[[], object]


class BackgroundState(State):
    """
    Background state is used to prevent other states from
    being required to track dirty screen areas. For example,
    in the start state, there is a menu on a blank background,
    since menus do not clean up dirty areas, the blank,
    "Background state" will do that. The alternative is creating
    a system for states to clean up their dirty screen areas.

    Eventually the need for this will be phased out.
    """

    def draw(self, surface: pygame.surface.Surface) -> None:
        surface.fill((0, 0, 0, 0))


class StartState(PopUpMenu[StartGameObj]):
    """The state responsible for the start menu."""

    escape_key_exits = False
    shrink_to_items = True

    def __init__(self) -> None:
        # If there is a save, then move the cursor to "Load game" first
        index = get_index_of_latest_save()
        super().__init__(selected_index=0 if index is None else 1)

        def change_state(
            state: Union[State, str],
            **change_state_kwargs: Any,
        ) -> Callable[[], State]:
            return partial(
                self.client.push_state,
                state,
                **change_state_kwargs,
            )

        def show_mod_menu() -> None:
            self.client.replace_state("ModChooserMenuState")

        def exit_game() -> None:
            self.client.exit = True

        menu_items_map = (
            ("menu_new_game", show_mod_menu),
            ("menu_load", change_state("LoadMenuState")),
            ("menu_options", change_state("ControlState")),
            ("exit", exit_game),
        )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)


class ModChooserMenuState(PopUpMenu[StartGameObj]):
    """This menu shows the 2 default mod campaigns at the moment."""

    shrink_to_items = True
    escape_key_exits = True

    def close(self) -> None:
        self.client.replace_state("StartState")

    def __init__(self) -> None:

        super().__init__()

        self.map_name = prepare.CONFIG.starting_map

        def new_game_callback(
            map_name: str,
        ) -> Callable:
            return partial(new_game, map_name)

        def set_player_name(text: str) -> None:
            map_path = prepare.fetch("maps", self.map_name)
            self.client.push_state("WorldState", map_name=map_path)
            self.client.push_state(FadeInTransition())
            local_session.player.name = text
            self.client.pop_state(self)

        def new_game(map_name: str) -> None:
            self.map_name = map_name
            # load the starting map
            self.client.push_state(
                InputMenu(
                    prompt=T.translate("input_name"),
                    callback=set_player_name,
                    escape_key_exits=True,
                    char_limit=prepare.PLAYER_NAME_LIMIT,
                )
            )
            self.client.push_state(FadeInTransition())

        # Build a menu of the default mod choices:
        menu_items_map: Tuple[Tuple[str, Callable], ...] = tuple()

        # If a different map has been passed as a parameter, show as an option:
        if prepare.CONFIG.starting_map != "player_house_bedroom.tmx":
            menu_items_map = menu_items_map + (
                (
                    str(prepare.CONFIG.starting_map),
                    new_game_callback(prepare.CONFIG.starting_map),
                ),
            )

        menu_items_map = menu_items_map + (
            ("spyder_campaign", new_game_callback("spyder_bedroom.tmx")),
            ("xero_campaign", new_game_callback("player_house_bedroom.tmx")),
            ("cancel", self.close),
        )

        for key, callback in menu_items_map:
            label = T.translate(key).upper()
            label = label.center(32)
            image = self.shadow_text(label)
            item = MenuItem(image, label, None, callback)
            self.add(item)
