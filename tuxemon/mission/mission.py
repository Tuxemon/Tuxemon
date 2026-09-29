# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from tuxemon.database.runtime import db
from tuxemon.db import (
    GameCondition,
    MissionModel,
    MissionStatus,
    MissionStepModel,
)
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC

logger = logging.getLogger(__name__)


class Mission:
    """Tuxemon mission."""

    def __init__(
        self,
        db_data: MissionModel,
        instance_id: UUID | None = None,
        completed_steps: set[str] | None = None,
        status: MissionStatus = MissionStatus.PENDING,
        assigned_to: str | None = None,
    ):
        self.slug = db_data.slug
        self._description_slug = db_data.description
        self.prerequisites = db_data.prerequisites
        self.connected_missions = db_data.connected_missions
        self.failure_conditions = db_data.failure_conditions
        self.required_items = db_data.required_items
        self.required_monsters = db_data.required_monsters
        self.required_missions = db_data.required_missions
        self.steps = {s.slug: s for s in db_data.steps.values()}
        self.repeatable = db_data.repeatable

        self.instance_id = instance_id or uuid4()
        self.completed_steps = completed_steps or set()
        self.status = status
        self.assigned_to = assigned_to

        self.generated: bool = False
        self._custom_name: str | None = None
        self._custom_description: str | None = None

    @property
    def name(self) -> str:
        if self._custom_name is not None:
            return self._custom_name
        return T.translate(self.slug) if self.slug else ""

    @name.setter
    def name(self, value: str) -> None:
        self._custom_name = value

    @property
    def description(self) -> str:
        if self._custom_description is not None:
            return self._custom_description
        return (
            T.translate(self._description_slug)
            if self._description_slug
            else ""
        )

    @description.setter
    def description(self, value: str) -> None:
        self._custom_description = value

    @classmethod
    def create(cls, slug: str) -> Mission:
        db_data = MissionModel.lookup(slug, db)
        return cls(db_data=db_data)

    @classmethod
    def from_save(cls, save_data: Mapping[str, Any]) -> Mission:
        slug = save_data["slug"]
        db_data = MissionModel.lookup(slug, db)

        return cls(
            db_data=db_data,
            instance_id=UUID(save_data["instance_id"]),
            completed_steps=set(save_data.get("completed_steps", [])),
            status=save_data.get("status", MissionStatus.PENDING),
            assigned_to=save_data.get("assigned_to"),
        )

    def update_status(self, new_status: MissionStatus) -> None:
        """Updates the mission's status."""
        self.status = new_status

    def get_state(self) -> Mapping[str, Any]:
        return {
            "slug": self.slug,
            "instance_id": self.instance_id.hex,
            "completed_steps": list(self.completed_steps),
            "status": self.status,
            "assigned_to": self.assigned_to,
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
            return True

        return all(
            character.variable_manager.check_conditions([prerequisite])
            for prerequisite in self.prerequisites
        )

    def check_failure_conditions(self, character: NPC) -> bool:
        if not self.failure_conditions:
            return False

        return all(
            character.variable_manager.check_conditions([condition])
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
        self, conditions_list: Sequence[GameCondition], character: NPC
    ) -> bool:
        if not conditions_list:
            return True

        return all(
            character.variable_manager.check_conditions([condition])
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

            if (
                step.auto_complete
                and base_conditions_met
                and any_of_met
                and all_of_met
            ):
                self.mark_step_completed(slug)

    def check_all_prerequisites(self, character: NPC) -> bool:
        return (
            self.check_required_missions(character)
            and check_items(character, self.required_items)
            and check_monsters(character, self.required_monsters)
            and self.check_prerequisites(character)
        )

    def is_active(self) -> bool:
        return self.status == MissionStatus.PENDING

    def is_completed(self) -> bool:
        return self.status == MissionStatus.COMPLETED

    def update_progress(self, character: NPC) -> None:
        if not self.is_active():
            return

        if self.check_failure_conditions(character):
            self.update_status(MissionStatus.FAILED)
            return

        if not self.check_all_prerequisites(character):
            return

        self.check_step_conditions(character)

        for step in self.get_active_steps():
            if step.slug in self.completed_steps:
                continue

            if not check_items(character, step.step_items_needed):
                continue

            if not check_monsters(character, step.step_monsters_needed):
                continue

        if self.get_progress() >= 100.0:
            self.update_status(MissionStatus.COMPLETED)

            if self.repeatable:
                self.completed_steps.clear()
                self.update_status(MissionStatus.PENDING)

    def validate_graph(self) -> None:
        visited = set()

        def dfs(slug: str) -> None:
            if slug in visited:
                raise ValueError(
                    f"Circular dependency detected at step {slug}"
                )
            visited.add(slug)
            for nxt in self.steps[slug].next_steps:
                if nxt not in self.steps:
                    continue
                dfs(nxt)
            visited.remove(slug)

        roots = self.get_root_steps()

        if not roots and self.steps:
            raise ValueError(
                "Circular dependency detected: no root steps found"
            )

        for root in roots:
            dfs(root)


def check_items(character: NPC, step_items: dict[str, int | None]) -> bool:
    for item_slug, required_quantity in step_items.items():
        item = character.bag.find_item(item_slug)
        if not item:
            return False
        if required_quantity is not None and item.quantity < required_quantity:
            return False
    return True


def check_monsters(
    character: NPC, step_monsters: dict[str, int | None]
) -> bool:
    for monster_slug, required_level in step_monsters.items():
        monster = character.party.find_monster(monster_slug)
        if not monster:
            return False
        if required_level is not None and monster.level < required_level:
            return False
    return True
