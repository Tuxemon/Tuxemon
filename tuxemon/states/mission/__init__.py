# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Options state"""
from __future__ import annotations

from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.db import MissionStatus
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.mission import Mission
from tuxemon.npc import NPC


class MissionState(PygameMenuState):
    """
    This state is responsible for the mission menu.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Used when initializing the state.
        """
        character: Optional[NPC] = None
        for element in kwargs.values():
            character = element["character"]
        if character is None:
            raise ValueError("No character found")
        self.character = character
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_MISSIONS)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(height=height, width=width)
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        missions: list[Mission] = []
        statuses = list(MissionStatus)
        for status in statuses:
            missions = [
                mission
                for mission in self.character.missions
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
