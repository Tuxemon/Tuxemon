# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.db import MissionStatus
from tuxemon.mission.manager import MissionManager
from tuxemon.mission.mission import Mission, check_items, check_monsters

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class MissionController:
    """Manages the missions for an NPC."""

    def __init__(
        self, character: NPC, mission_manager: MissionManager
    ) -> None:
        self.character = character
        self.mission_manager = mission_manager

    def encode_missions(self) -> Sequence[Mapping[str, Any]]:
        """
        Prepares a list of missions to be saved to a file.
        """
        return encode_mission(self.get_missions())

    def decode_missions(
        self, save_data: Optional[Sequence[Mapping[str, Any]]]
    ) -> None:
        """
        Recreates missions from saved data.
        """
        self.mission_manager.missions = {}
        if save_data:
            for mission_data in decode_mission(save_data):
                if mission_data.assigned_to in (None, self.character.slug):
                    self.mission_manager.add_mission(mission_data)

    def assign_mission(self, mission: Mission) -> None:
        """Assigns a mission to this character."""
        mission.assigned_to = self.character.slug
        self.mission_manager.add_mission(mission)

    def check_all_prerequisites(self) -> bool:
        """
        Checks if all prerequisites for all missions are met for the given character.
        """
        return all(
            mission.check_all_prerequisites(self.character)
            for mission in self.get_missions()
        )

    def update_mission_progress(self) -> None:
        """
        Updates the progress of all missions for the given character.
        """
        for mission in self.get_missions():
            if not mission.is_active():
                continue

            if mission.check_failure_conditions(self.character):
                mission.update_status(MissionStatus.failed)
                continue

            if not mission.check_all_prerequisites(self.character):
                continue

            for step_slug, step in mission.steps.items():
                if step_slug in mission.completed_steps:
                    continue

                # Check step-specific requirements
                if not check_items(self.character, step.step_items_needed):
                    continue
                if not check_monsters(
                    self.character, step.step_monsters_needed
                ):
                    continue

                if mission.get_progress() >= 100.0:
                    mission.update_status(MissionStatus.completed)

                    if mission.repeatable:
                        mission.completed_steps.clear()
                        mission.update_status(MissionStatus.pending)

    def get_missions_with_met_prerequisites(self) -> list[Mission]:
        """
        Checks for missions with met prerequisites.
        """
        return [
            mission
            for mission in self.get_active_missions()
            if mission.check_all_prerequisites(self.character)
        ]

    def check_connected_missions(self) -> bool:
        """
        Checks if all connected missions are accessible for the given character.
        """
        return all(
            mission.check_connected_missions(self.character)
            for mission in self.get_missions()
        )

    def get_missions(self) -> list[Mission]:
        """
        Retrieves all missions through the mission manager.
        """
        return self.mission_manager.get_missions_for(self.character.slug)

    def get_active_missions(self) -> list[Mission]:
        """
        Retrieves all active missions through the mission manager.
        """
        return [
            mission for mission in self.get_missions() if mission.is_active()
        ]

    def is_step_unlocked(self, mission_slug: str, step_slug: str) -> bool:
        mission = self.mission_manager.find_mission(mission_slug)
        if mission:
            return mission.is_step_unlocked(step_slug)
        return False

    def get_next_available_steps(self, mission_slug: str) -> list[str]:
        mission = self.mission_manager.find_mission(mission_slug)
        if not mission:
            return []

        return [
            slug
            for slug in mission.steps
            if mission.is_step_unlocked(slug)
            and slug not in mission.completed_steps
        ]


def decode_mission(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Mission]:
    missions = []
    for mission_data in json_data or []:
        mission = Mission.from_db(mission_data["slug"])
        if mission:
            mission.set_state(mission_data)
            missions.append(mission)
        else:
            logger.warning(
                f"Mission with slug '{mission_data['slug']}' not found in database."
            )
    return missions


def encode_mission(missions: Sequence[Mission]) -> Sequence[Mapping[str, Any]]:
    return [mission.get_state() for mission in missions]
