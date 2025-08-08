# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.db import MissionStatus
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.mission.mission import Mission
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

MenuGameObj = Callable[[], object]


class MissionState(PygameMenuState):
    """
    This state is responsible for the mission menu.
    """

    def __init__(self, character: NPC) -> None:
        self.character = character
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_MISSIONS)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        width = int(0.8 * width)
        height = int(0.8 * height)
        super().__init__(height=height, width=width)
        self.character.mission_controller.update_mission_progress()
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        missions = self.character.mission_controller.get_active_missions()

        missions.sort(key=lambda m: m.slug)

        for key, mission in enumerate(missions, start=1):
            if not mission.check_all_prerequisites(self.character):
                continue

            progress = round(mission.get_progress(), 1)
            repeatable = "@" if mission.repeatable else ""
            label = f"{key}. {mission.name}{repeatable} ({progress}%)"

            menu.add.button(
                title=label,
                action=change_state(
                    "SingleMissionState",
                    mission=mission,
                    character=self.character,
                ),
                font_size=self.font_type.small,
            )


class SingleMissionState(PygameMenuState):
    def __init__(self, mission: Mission, character: NPC) -> None:
        self.mission = mission
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
        def delete_mission() -> None:
            msg = T.translate("mission_deletion")
            open_dialog(self.client, [msg])

            options = [
                ChoiceOption(
                    key="no",
                    display_text=T.translate("no"),
                    action=refuse_deletion,
                ),
                ChoiceOption(
                    key="yes",
                    display_text=T.translate("yes"),
                    action=confirm_deletion,
                ),
            ]

            menu = MenuOptions(options)

            open_choice_dialog(self.client, menu)

        def confirm_deletion() -> None:
            self.mission.update_status(MissionStatus.removed)
            self.character.mission_controller.mission_manager.remove_by_slug(
                self.mission.slug
            )
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("DialogState")
            self.client.remove_state_by_name("SingleMissionState")
            self.client.remove_state_by_name("WorldMenuState")
            self.client.remove_state_by_name("MissionState")

        def refuse_deletion() -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("DialogState")

        menu.add.label(
            title=f"{self.mission.name}",
            label_id="name",
            font_size=self.font_type.small,
            align=locals.ALIGN_LEFT,
            float=False,
        )

        menu.add.label(
            title=self.mission.description,
            label_id="description",
            font_size=self.font_type.small,
            align=locals.ALIGN_LEFT,
            float=False,
        )

        if self.mission.repeatable:
            menu.add.label(
                title=T.translate("mission_repeatable"),
                font_size=self.font_type.small,
                align=locals.ALIGN_LEFT,
            )

        next_missions = (
            ", ".join(m["slug"] for m in self.mission.connected_missions)
            if self.mission.connected_missions
            else "-"
        )
        menu.add.label(
            title=f"{T.translate('mission_next')}: {next_missions}",
            label_id="next_missions",
            font_size=self.font_type.small,
            align=locals.ALIGN_LEFT,
            float=False,
        )

        progress = self.mission.get_progress()
        menu.add.progress_bar(
            title=T.translate("mission_progress"),
            default=progress,
            font_size=self.font_type.small,
            align=locals.ALIGN_LEFT,
            float=False,
        )

        menu.add.button(
            title=T.translate("mission_delete"),
            action=delete_mission,
            font_size=self.font_type.small,
        )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        client = self.client
        missions = self.character.mission_controller.get_active_missions()
        if event.button in (buttons.RIGHT, buttons.LEFT) and event.pressed:
            if len(missions) == 1:
                return None
            current_index = missions.index(self.mission)
            new_index = (
                (current_index + 1) % len(missions)
                if event.button == buttons.RIGHT
                else (current_index - 1) % len(missions)
            )
            client.replace_state(
                "SingleMissionState",
                mission=missions[new_index],
                character=self.character,
            )
        elif event.button in (buttons.BACK, buttons.B) and event.pressed:
            client.remove_state_by_name("SingleMissionState")
        elif event.button == buttons.A and event.pressed:
            super().process_event(event)
        return None
