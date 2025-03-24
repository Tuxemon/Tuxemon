# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.db import MissionStatus, db
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.npc import NPC

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "status",
)


@dataclass
class MissionProgress:
    game_variables: dict[str, Any]
    completion_percentage: float


class MissionManager:
    def __init__(self, character: NPC) -> None:
        self.character = character
        self.missions: list[Mission] = []

    def add_mission(self, mission: Mission) -> None:
        """
        Adds a mission.
        """
        self.missions.append(mission)

    def remove_mission(self, mission: Mission) -> None:
        """
        Removes a mission.
        """
        self.missions.remove(mission)

    def find_mission(self, mission: str) -> Optional[Mission]:
        """
        Finds a mission.
        """
        return next(
            (mis for mis in self.missions if mis.slug == mission), None
        )

    def get_mission_count(self) -> int:
        return len(self.missions)

    def encode_missions(self) -> Sequence[Mapping[str, Any]]:
        return encode_mission(self.missions)

    def load_missions(
        self, save_data: Optional[Sequence[Mapping[str, Any]]]
    ) -> None:
        self.missions = decode_mission(save_data)

    def check_all_prerequisites(self) -> bool:
        """
        Checks if all prerequisites for all missions are met for the given character.
        """
        return all(
            mission.check_all_prerequisites(self.character)
            for mission in self.missions
        )

    def update_mission_progress(self) -> None:
        """
        Updates the progress of all missions for the given character.
        """
        for mission in self.missions:
            if (
                mission.check_all_prerequisites(self.character)
                and mission.is_active()
            ):
                if mission.get_progress(self.character) >= 100.0:
                    mission.update_status(MissionStatus.completed)

    def get_missions_with_met_prerequisites(self) -> list[Mission]:
        """
        Checks for missions with met prerequisites.
        """
        missions_with_met_prerequisites = []
        for mission in self.missions:
            if (
                mission.check_all_prerequisites(self.character)
                and mission.is_active()
            ):
                missions_with_met_prerequisites.append(mission)
        return missions_with_met_prerequisites

    def check_connected_missions(self) -> bool:
        """
        Checks if all connected missions are accessible for the given character.
        """
        return all(
            mission.check_connected_missions(self.character)
            for mission in self.missions
        )

    def get_active_missions(self) -> list[Mission]:
        return [mission for mission in self.missions if mission.is_active()]


class Mission:
    """
    Tuxemon mission.

    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}
        self.slug: str = ""
        self.name: str = ""
        self.description: str = ""
        self.prerequisites: Sequence[dict[str, Any]] = []
        self.connected_missions: Sequence[dict[str, Any]] = []
        self.progress: Sequence[MissionProgress] = []
        self.required_items: Sequence[str] = []
        self.required_monsters: Sequence[str] = []
        self.required_missions: Sequence[str] = []
        self.status: MissionStatus = MissionStatus.pending
        self.instance_id = uuid.uuid4()
        self.set_state(save_data)

    def load(self, slug: str) -> None:
        """
        Loads and sets mission from the db.

        """
        try:
            results = db.lookup(slug, table="mission")
        except KeyError:
            raise RuntimeError(f"Mission {slug} not found")

        self.slug = results.slug
        self.name = T.translate(results.slug)
        self.description = T.translate(results.description)
        self.prerequisites = results.prerequisites
        self.connected_missions = results.connected_missions
        if isinstance(results.progress, list):
            self.progress = [
                MissionProgress(**p.model_dump()) for p in results.progress
            ]
        else:
            raise ValueError(
                "Expected results.progress to be a list of dictionaries"
            )
        self.required_items = results.required_items
        self.required_monsters = results.required_monsters
        self.required_missions = results.required_missions
        self.status = self.status

    def update_status(self, new_status: MissionStatus) -> None:
        """
        Updates the mission's status.
        """
        self.status = new_status

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the mission to be saved to a file.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = str(self.instance_id.hex)

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        """
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)

    def check_required_items(self, character: NPC) -> bool:
        return all(character.find_item(item) for item in self.required_items)

    def check_required_monsters(self, character: NPC) -> bool:
        return all(
            character.find_monster(monster)
            for monster in self.required_monsters
        )

    def get_slug_missions(self, character: NPC) -> list[str]:
        return [mission.slug for mission in character.mission_manager.missions]

    def check_connected_missions(self, character: NPC) -> bool:
        return all(
            mission in self.get_slug_missions(character)
            for mission in [m["slug"] for m in self.connected_missions]
        )

    def check_required_missions(self, character: NPC) -> bool:
        return all(
            mission in self.get_slug_missions(character)
            for mission in self.required_missions
        )

    def check_prerequisites(self, character: NPC) -> bool:
        return all(
            all(
                key in character.game_variables
                and character.game_variables[key] == value
                for key, value in prerequisite.items()
            )
            for prerequisite in self.prerequisites
        )

    def get_progress(self, character: NPC) -> float:
        if not self.progress:
            return 0.0

        total_completion = 0.0
        count = 0

        for progress in self.progress:
            if all(
                key in character.game_variables
                and character.game_variables[key] == value
                for key, value in progress.game_variables.items()
            ):
                total_completion += progress.completion_percentage
                count += 1

        return total_completion / count if count > 0 else 0.0

    def get_progress_count(self, character: NPC) -> int:
        return sum(
            all(
                key in character.game_variables
                and character.game_variables[key] == value
                for key, value in progress.game_variables.items()
            )
            for progress in self.progress
        )

    def check_all_prerequisites(self, character: NPC) -> bool:
        return (
            self.check_required_missions(character)
            and self.check_required_items(character)
            and self.check_required_monsters(character)
            and self.check_prerequisites(character)
        )

    def is_active(self) -> bool:
        return self.status == MissionStatus.pending


def decode_mission(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Mission]:
    return [Mission(save_data=mission) for mission in json_data or {}]


def encode_mission(missions: Sequence[Mission]) -> Sequence[Mapping[str, Any]]:
    return [mission.get_state() for mission in missions]
