# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Options state"""
from __future__ import annotations

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import prepare, tools
from tuxemon.db import MissionStatus
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.mission import Mission
from tuxemon.session import local_session


class MissionState(PygameMenuState):
    """
    This state is responsible for the mission menu.
    """

    def __init__(self) -> None:
        """
        Used when initializing the state.
        """
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(prepare.BG_MISSIONS),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(height=height, width=width)
        self.initialize_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        player = local_session.player

        missions: list[Mission] = []
        statuses = list(MissionStatus)
        for status in statuses:
            missions = [
                mission
                for mission in player.missions
                if mission.status == status
            ]
            _status = T.translate(status)
            _nr_mission = len(missions)
            menu.add.label(f"{_status} ({_nr_mission})")
            for key, mission in enumerate(missions, start=1):
                label = f"{key}. {mission.name}"
                menu.add.button(
                    title=label,
                    action=None,
                    font_size=self.font_size_small,
                )
