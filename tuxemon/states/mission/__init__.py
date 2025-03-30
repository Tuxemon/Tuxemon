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
from tuxemon.mission import Mission
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.tools import open_choice_dialog, open_dialog

MenuGameObj = Callable[[], object]


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
        self.character.mission_manager.update_mission_progress()
        self.initialize_items(self.menu)
        self.reset_theme()

    def initialize_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        missions = self.character.mission_manager.get_active_missions()
        for key, mission in enumerate(missions, start=1):
            if mission.check_all_prerequisites(self.character):
                progress = mission.get_progress(self.character)
                label = f"{key}. {mission.name} ({round(progress, 1)}%)"
                menu.add.button(
                    title=label,
                    action=change_state(
                        "SingleMissionState",
                        kwargs={
                            "mission": mission,
                            "character": self.character,
                        },
                    ),
                    font_size=self.font_size_small,
                )


class SingleMissionState(PygameMenuState):
    def __init__(self, **kwargs: Any) -> None:
        mission: Optional[Mission] = None
        character: Optional[NPC] = None
        for element in kwargs.values():
            mission = element["mission"]
            character = element["character"]
        if mission is None or character is None:
            raise ValueError("No mission")
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
            open_dialog(local_session, [msg])
            _no = T.translate("no")
            _yes = T.translate("yes")
            menu: list[tuple[str, str, Callable[[], None]]] = []
            menu.append(("no", _no, refuse_deletion))
            menu.append(("yes", _yes, confirm_deletion))
            open_choice_dialog(local_session, menu)

        def confirm_deletion() -> None:
            self.mission.update_status(MissionStatus.failed)
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("DialogState")
            self.client.remove_state_by_name("SingleMissionState")
            self.client.remove_state_by_name("WorldMenuState")
            self.client.pop_state()

        def refuse_deletion() -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.pop_state()

        missions = self.character.mission_manager.get_active_missions()

        single = missions.index(self.mission)
        menu.add.label(
            title=f"{single + 1}/{len(missions)}",
            label_id="number",
            font_size=self.font_size_small,
            align=locals.ALIGN_RIGHT,
            float=False,
        )
        menu.add.label(
            title=f"{self.mission.name}",
            label_id="name",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=False,
        )
        menu.add.label(
            title=self.mission.description,
            label_id="description",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=False,
        )
        next_missions = (
            ", ".join(m["slug"] for m in self.mission.connected_missions)
            if self.mission.connected_missions
            else "-"
        )
        menu.add.label(
            title=f"Next missions: {next_missions}",
            label_id="next_missions",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=False,
        )
        progress = self.mission.get_progress(self.character)
        menu.add.progress_bar(
            title="Progress",
            default=progress,
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=False,
        )
        menu.add.button(
            title="Delete",
            action=delete_mission,
            font_size=self.font_size_small,
        )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        client = self.client
        missions = self.character.mission_manager.get_active_missions()
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
                kwargs={
                    "mission": missions[new_index],
                    "character": self.character,
                },
            )
        elif event.button in (buttons.BACK, buttons.B) and event.pressed:
            client.pop_state()
        elif event.button == buttons.A and event.pressed:
            super().process_event(event)
        return None
