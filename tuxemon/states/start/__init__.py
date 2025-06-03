# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Start state."""
from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import Any, Optional, Union

import pygame_menu
from pygame.surface import Surface
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.save import get_index_of_latest_save
from tuxemon.session import local_session
from tuxemon.state import State
from tuxemon.time_handler import today_ordinal

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

    def draw(self, surface: Surface) -> None:
        surface.fill(prepare.BLACK_COLOR)


class StartState(PygameMenuState):
    """The state responsible for the start menu."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        # If there is a save, then move the cursor to "Load game" first
        index = get_index_of_latest_save()
        config = prepare.CONFIG

        def new_game() -> None:
            destination = f"{prepare.STARTING_MAP}{config.mods[0]}.tmx"
            map_path = prepare.fetch("maps", destination)
            self.client.push_state(
                "WorldState", session=local_session, map_name=map_path
            )
            game_var = local_session.player.game_variables
            game_var["date_start_game"] = today_ordinal()
            self.client.pop_state(self)

        def change_state(
            state: Union[State, str],
            **change_state_kwargs: Any,
        ) -> Callable[[], State]:
            return partial(
                self.client.push_state,
                state,
                **change_state_kwargs,
            )

        def exit_game() -> None:
            self.client.quit()

        if index is not None:
            menu.add.button(
                title=T.translate("menu_load"),
                action=change_state("LoadMenuState"),
                font_size=self.font_size_big,
                button_id="menu_load",
            )
        if len(config.mods) == 1:
            menu.add.button(
                title=T.translate("menu_new_game"),
                action=new_game,
                font_size=self.font_size_big,
                button_id="menu_new_game",
            )
        else:
            menu.add.button(
                title=T.translate("menu_new_game"),
                action=change_state("ModsChoice", mods=config.mods),
                font_size=self.font_size_big,
                button_id="menu_mod_choice",
            )
        menu.add.button(
            title=T.translate("menu_minigame"),
            action=change_state("MinigameState"),
            font_size=self.font_size_big,
            button_id="menu_minigame",
        )
        menu.add.button(
            title=T.translate("menu_options"),
            action=change_state("ControlState", main_menu=True),
            font_size=self.font_size_big,
            button_id="menu_options",
        )
        menu.add.button(
            title=T.translate("exit"),
            action=exit_game,
            font_size=self.font_size_big,
            button_id="exit",
        )

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_START_SCREEN)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if (
            event.button in (buttons.HOME, buttons.BACK, buttons.B)
            and event.pressed
        ):
            return None
        else:
            return super().process_event(event)


class ModsChoice(PygameMenuState):
    """The state responsible for the mods menu."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:

        def new_game(mod_name: str) -> None:
            destination = f"{prepare.STARTING_MAP}{mod_name}.tmx"
            map_path = prepare.fetch("maps", destination)
            self.client.push_state(
                "WorldState", session=local_session, map_name=map_path
            )
            game_var = local_session.player.game_variables
            game_var["date_start_game"] = today_ordinal()
            self.client.pop_state(self)

        for mod_name in self.mods:
            menu.add.button(
                title=T.translate(f"{mod_name}_campaign"),
                action=partial(new_game, mod_name),
                font_size=self.font_size_big,
                button_id=mod_name,
            )

    def __init__(self, mods: list[str]) -> None:
        self.mods = mods
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_START_SCREEN)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.reset_theme()
