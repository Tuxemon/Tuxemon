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


class Mission:
    """Tuxemon mission."""

    def __init__(self) -> None:
        self.slug: str = ""
        self.name: str = ""
        self.description: str = ""
        self.generated: bool = False
        self.prerequisites: Sequence[dict[str, Any]] = []
        self.connected_missions: Sequence[dict[str, Any]] = []
        self.failure_conditions: Sequence[dict[str, Any]] = []
        self.required_items: dict[str, Optional[int]] = {}
        self.required_monsters: dict[str, Optional[int]] = {}
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
        save_data["instance_id"] = self.instance_id.hex
        save_data["completed_steps"] = list(self.completed_steps)
        save_data["assigned_to"] = self.assigned_to

        if self.generated and self.steps:
            save_data["steps"] = {
                slug: step.model_dump() for slug, step in self.steps.items()
            }

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
        self.generated = save_data.get("generated", False)

        for key in SIMPLE_PERSISTANCE_ATTRIBUTES:
            if key in save_data:
                setattr(self, key, save_data[key])

        if self.generated and "steps" in save_data:
            self.steps = {
                slug: MissionStepModel.model_validate(step_data)
                for slug, step_data in save_data["steps"].items()
            }

    def mark_step_completed(self, slug: str) -> None:
        if slug in self.steps:
            self.completed_steps.add(slug)

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
                character.game_variables.has(key)
                and character.game_variables.get(key) == value
                for key, value in prerequisite.items()
            )
            for prerequisite in self.prerequisites
        )

    def check_failure_conditions(self, character: NPC) -> bool:
        if not self.failure_conditions:
            return False  # No failure conditions means nothing can fail

        return all(
            all(
                character.game_variables.has(key)
                and character.game_variables.get(key) == value
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
            and check_items(character, self.required_items)
            and check_monsters(character, self.required_monsters)
            and self.check_prerequisites(character)
        )

    def is_active(self) -> bool:
        return self.status == MissionStatus.pending

    def is_completed(self) -> bool:
        return self.status == MissionStatus.completed


def check_items(character: NPC, step_items: dict[str, Optional[int]]) -> bool:
    for item_slug, required_quantity in step_items.items():
        item = character.bag.find_item(item_slug)
        if not item:
            return False
        if required_quantity is not None and item.quantity < required_quantity:
            return False
    return True


def check_monsters(
    character: NPC, step_monsters: dict[str, Optional[int]]
) -> bool:
    for monster_slug, required_level in step_monsters.items():
        monster = character.party.find_monster(monster_slug)
        if not monster:
            return False
        if required_level is not None and monster.level < required_level:
            return False
    return True
