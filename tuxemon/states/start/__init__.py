# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Start state.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import Any, Union

import pygame
import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import formula, prepare, tools
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.save import get_index_of_latest_save
from tuxemon.session import local_session
from tuxemon.state import State

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


class StartState(PygameMenuState):
    """The state responsible for the start menu."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        # If there is a save, then move the cursor to "Load game" first
        index = get_index_of_latest_save()
        self.menu._onclose = None

        def new_game() -> None:
            map_path = prepare.fetch("maps", prepare.STARTING_MAP)
            self.client.push_state("WorldState", map_name=map_path)
            local_session.player.game_variables[
                "date_start_game"
            ] = formula.today_ordinal()
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
            self.client.exit = True

        self.menu._last_selected_type
        if index is not None:
            menu.add.button(
                title=T.translate("menu_load"),
                action=change_state("LoadMenuState"),
                font_size=self.font_size_big,
                button_id="menu_load",
            )
        menu.add.button(
            title=T.translate("menu_new_game"),
            action=new_game,
            font_size=self.font_size_big,
            button_id="menu_new_game",
        )
        menu.add.button(
            title=T.translate("menu_minigame"),
            action=change_state("MinigameState"),
            font_size=self.font_size_big,
            button_id="menu_minigame",
        )
        menu.add.button(
            title=T.translate("exit"),
            action=exit_game,
            font_size=self.font_size_big,
            button_id="exit",
        )

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/bg_pcstate.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT
