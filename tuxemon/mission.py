# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon.db import MissionModel, MissionStatus, MissionStepModel, db
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "status",
)


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

            if mission.check_all_prerequisites(self.character):
                mission.check_step_conditions(self.character)

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


class MissionManager:
    def __init__(self) -> None:
        self.missions: dict[str, Mission] = {}

    def assign_mission_to(self, mission: Mission, npc_slug: str) -> None:
        mission.assigned_to = npc_slug
        self.add_mission(mission)

    def add_mission(self, mission: Mission) -> None:
        if mission.slug not in self.missions:
            self.missions[mission.slug] = mission

    def remove_mission(self, mission: Mission) -> None:
        self.missions.pop(mission.slug, None)

    def remove_by_slug(self, slug: str) -> None:
        self.missions.pop(slug, None)

    def find_mission(self, slug: str) -> Optional[Mission]:
        return self.missions.get(slug)

    def get_mission_count(self) -> int:
        return len(self.missions)

    def get_active_missions(self) -> list[Mission]:
        return [m for m in self.missions.values() if m.is_active()]

    def get_completed_missions(self) -> list[Mission]:
        return [m for m in self.missions.values() if m.is_completed()]

    def get_missions_by_status(self, status: MissionStatus) -> list[Mission]:
        return [m for m in self.missions.values() if m.status == status]

    def get_missions_for(self, npc_slug: str) -> list[Mission]:
        return [
            m
            for m in self.missions.values()
            if m.assigned_to in (None, npc_slug)
            and m.status != MissionStatus.removed
        ]


class Mission:
    """Tuxemon mission."""

    def __init__(self) -> None:
        self.slug: str = ""
        self.name: str = ""
        self.description: str = ""
        self.prerequisites: Sequence[dict[str, Any]] = []
        self.connected_missions: Sequence[dict[str, Any]] = []
        self.failure_conditions: Sequence[dict[str, Any]] = []
        self.required_items: Sequence[str] = []
        self.required_monsters: Sequence[str] = []
        self.required_missions: Sequence[str] = []
        self.steps: dict[str, MissionStepModel] = {}
        self.completed_steps: set[str] = set()
        self.assigned_to: Optional[str] = None
        self.repeatable: bool = False
        self.status: MissionStatus = MissionStatus.pending
        self.instance_id: UUID = uuid4()

    @classmethod
    def from_db(cls, slug: str) -> Mission:
        """Creates a new Mission instance loaded from the database."""
        try:
            results = MissionModel.lookup(slug, db)
        except LookupError as e:
            raise LookupError(f"Mission with slug '{slug}' not found.") from e

        mission = cls()
        mission.slug = results.slug
        mission.name = T.translate(results.slug)
        mission.description = T.translate(results.description)
        mission.prerequisites = results.prerequisites
        mission.connected_missions = results.connected_missions
        mission.required_items = results.required_items
        mission.required_monsters = results.required_monsters
        mission.required_missions = results.required_missions
        mission.steps = {s.slug: s for s in results.steps.values()}
        mission.repeatable = results.repeatable
        mission.failure_conditions = results.failure_conditions
        return mission

    def load(self, slug: str) -> None:
        """
        Loads and sets mission from the db.
        """
        results = MissionModel.lookup(slug, db)
        self.slug = results.slug
        self.name = T.translate(results.slug)
        self.description = T.translate(results.description)
        self.prerequisites = results.prerequisites
        self.connected_missions = results.connected_missions
        self.required_items = results.required_items
        self.required_monsters = results.required_monsters
        self.required_missions = results.required_missions
        self.steps = {s.slug: s for s in results.steps.values()}
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
        save_data["completed_steps"] = list(self.completed_steps)
        save_data["assigned_to"] = self.assigned_to
        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.
        """
        if not save_data:
            return

        self.instance_id = UUID(save_data.get("instance_id", uuid4().hex))
        self.completed_steps = set(save_data.get("completed_steps", []))
        self.assigned_to = save_data.get("assigned_to", None)

        for key in SIMPLE_PERSISTANCE_ATTRIBUTES:
            if key in save_data:
                setattr(self, key, save_data[key])

    def mark_step_completed(self, slug: str) -> None:
        if slug in self.steps:
            self.completed_steps.add(slug)

    def check_required_items(self, character: NPC) -> bool:
        return all(
            character.items.find_item(item) for item in self.required_items
        )

    def check_required_monsters(self, character: NPC) -> bool:
        return all(
            character.party.find_monster(monster)
            for monster in self.required_monsters
        )

    def get_slug_missions(self, character: NPC) -> list[str]:
        return [
            mission.slug
            for mission in character.mission_controller.get_missions()
        ]

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
        if not self.prerequisites:
            return True  # No prerequisites means it's allowed

        return all(
            all(
                key in character.game_variables
                and character.game_variables[key] == value
                for key, value in prerequisite.items()
            )
            for prerequisite in self.prerequisites
        )

    def check_failure_conditions(self, character: NPC) -> bool:
        if not self.failure_conditions:
            return False  # No failure conditions means nothing can fail

        return all(
            all(
                key in character.game_variables
                and character.game_variables[key] == value
                for key, value in condition.items()
            )
            for condition in self.failure_conditions
        )

    def get_progress(self) -> float:
        if not self.steps or not self.completed_steps:
            return 0.0

        completed_orders = {
            self.steps[slug].order
            for slug in self.completed_steps
            if slug in self.steps and not self.steps[slug].optional
        }

        all_orders = {
            step.order for step in self.steps.values() if not step.optional
        }

        return (len(completed_orders) / max(len(all_orders), 1)) * 100.0

    def get_active_steps(self) -> list[MissionStepModel]:
        return [
            s for k, s in self.steps.items() if k not in self.completed_steps
        ]

    def get_root_steps(self) -> set[str]:
        """
        Dynamically determines which steps are the starting points of the
        mission.
        """
        all_next_steps = {
            ns for step in self.steps.values() for ns in step.next_steps
        }
        return set(self.steps.keys()) - all_next_steps

    def is_step_unlocked(self, slug: str) -> bool:
        """
        Checks if a mission step is currently available to be completed.
        A step is unlocked if it's a starting step or a next step of a
        completed step.
        """
        if slug not in self.steps:
            return False

        # Check if it's a root step
        if slug in self.get_root_steps():
            return True

        # Check if it's a 'next step' of a completed step
        return any(
            slug in self.steps[s].next_steps
            for s in self.completed_steps
            if s in self.steps
        )

    def _check_conditions_list(
        self, conditions_list: Sequence[dict[str, Any]], character: NPC
    ) -> bool:
        if not conditions_list:
            return True
        return all(
            all(
                character.game_variables.get(k) == v
                for k, v in condition.items()
            )
            for condition in conditions_list
        )

    def check_step_conditions(self, character: NPC) -> None:
        for slug, step in self.steps.items():
            if slug in self.completed_steps:
                continue

            base_conditions_met = self._check_conditions_list(
                [step.conditions], character
            )
            any_of_met = self._check_conditions_list(step.any_of, character)
            all_of_met = self._check_conditions_list(step.all_of, character)

            if base_conditions_met and any_of_met and all_of_met:
                self.mark_step_completed(slug)

    def check_all_prerequisites(self, character: NPC) -> bool:
        return (
            self.check_required_missions(character)
            and self.check_required_items(character)
            and self.check_required_monsters(character)
            and self.check_prerequisites(character)
        )

    def is_active(self) -> bool:
        return self.status == MissionStatus.pending

    def is_completed(self) -> bool:
        return self.status == MissionStatus.completed


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
