# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from tuxemon.constants import paths
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.database.runtime import db
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.db import MonsterModel

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

lookup_cache: dict[str, MonsterModel] = {}


@dataclass
class ActionConfig:
    trigger: float = 0.0
    level_bounds: tuple[int, int] = (0, 0)
    failure_dialog: str = "fishing_rod_failure"
    stages: list[str] = field(default_factory=list)
    stage_weights: dict[str, float] = field(default_factory=dict)
    shapes: list[str] = field(default_factory=list)
    shape_weights: dict[str, float] = field(default_factory=dict)
    types: list[str] = field(default_factory=list)
    type_weights: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    tag_shape: dict[str, float] = field(default_factory=dict)
    animation_color: list[int] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    held_items: dict[str, float] = field(default_factory=dict)
    exp_req_mod: float | None = None
    cast_time: float = 1.0
    wait_time: float = 2.0
    bite_time: float = 1.0
    encounter_time: float = 0.5

    def validate_parameters(self) -> None:
        if not (0 <= self.trigger <= 1):
            raise ValueError("Trigger must be between 0 and 1 inclusive.")
        if self.level_bounds[0] < 0 or self.level_bounds[1] < 0:
            raise ValueError("Bounds must be non-negative.")
        if self.level_bounds[0] > self.level_bounds[1]:
            raise ValueError("Lower bound cannot exceed upper bound.")


class Loader:
    _config_fishing: dict[str, ActionConfig] = {}

    @classmethod
    def get_config_fishing(cls, filename: str) -> dict[str, ActionConfig]:
        yaml_path = paths.mods_folder / filename
        if not cls._config_fishing:
            raw_map = load_yaml(yaml_path)
            cls._config_fishing = {
                key: ActionConfig(**item) for key, item in raw_map.items()
            }
        return cls._config_fishing


class FishingStage(Enum):
    CAST = 1
    WAIT = 2
    BITE = 3
    ENCOUNTER = 4
    DONE = 5


@dataclass
class FishingEffect(CoreEffect):
    """
    Applies the "fishing" effect when using a fishing item.

    This effect initiates a staged fishing sequence that may result in a
    wild monster encounter. The sequence progresses through several phases
    (cast, wait, bite, encounter, done) with configurable timings and
    probabilities defined in external YAML configuration.

    **Example**

    .. code-block:: json

        "effects": [
            "fishing"
        ]
    """

    name = "fishing"
    stage: FishingStage = FishingStage.CAST
    _elapsed: float = 0.0
    _duration: float = 0.0
    _pending_encounter: tuple[str, int] | None = None
    _trigger_next_frame: bool = False

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_monsters()

        fishing_configs = Loader.get_config_fishing(f"{self.name}.yaml")

        self._fish: ActionConfig = fishing_configs[item.slug]
        self._fish.validate_parameters()

        monster_slugs = self._get_fishing_monsters()

        if monster_slugs and random.random() <= self._fish.trigger:
            mon_slug = monster_slugs[0]
            low, high = self._fish.level_bounds
            level = random.randint(low, high)
            self._pending_encounter = (mon_slug, level)

        self.stage = FishingStage.CAST
        self._elapsed = 0.0
        self._duration = self._fish.cast_time
        return ItemEffectResult(name=item.name, success=True)

    def update(self, session: Session, dt: float) -> None:
        session.client.push_state("SinkState")
        if self.stage == FishingStage.DONE:
            return

        self._elapsed += dt

        if self.stage == FishingStage.CAST and self._elapsed >= self._duration:
            self.stage = FishingStage.WAIT
            self._elapsed = 0.0
            self._duration = self._fish.wait_time

        elif (
            self.stage == FishingStage.WAIT and self._elapsed >= self._duration
        ):
            self.stage = FishingStage.BITE
            self._elapsed = 0.0
            self._duration = self._fish.bite_time

        elif (
            self.stage == FishingStage.BITE and self._elapsed >= self._duration
        ):
            if self._pending_encounter:
                self._trigger_next_frame = True
            self.stage = FishingStage.ENCOUNTER
            self._elapsed = 0.0
            self._duration = self._fish.encounter_time

        elif (
            self.stage == FishingStage.ENCOUNTER
            and self._elapsed >= self._duration
        ):
            if self._trigger_next_frame and self._pending_encounter:
                mon_slug, level = self._pending_encounter
                exp_req_mod = self._fish.exp_req_mod
                env = (
                    self._fish.environment.get("night")
                    if session.time.get_time_variables().stage_of_day
                    == "night"
                    else self._fish.environment.get("default")
                )
                env = env or "ocean"
                session.client.environment_manager.load_environment(env)
                session.client.environment_manager.lock_environment()
                rgb = ":".join(map(str, self._fish.animation_color))
                held_item = None
                if self._fish.held_items:
                    items, weights = zip(*self._fish.held_items.items())
                    held_item = random.choices(items, weights=weights, k=1)[0]

                session.client.event_engine.execute_action(
                    "wild_encounter",
                    [
                        mon_slug,
                        level,
                        exp_req_mod,
                        None,
                        rgb,
                        held_item,
                    ],
                    True,
                )
                self._pending_encounter = None
                self._trigger_next_frame = False
            else:
                dialog_key = self._fish.failure_dialog
                session.client.event_engine.execute_action(
                    "translated_dialog", [dialog_key], True
                )
                logger.info("Fishing attempt ended with no catch.")
            session.client.remove_state_by_name("SinkState")
            self.stage = FishingStage.DONE

    def is_finished(self) -> bool:
        return self.stage == FishingStage.DONE

    def _get_fishing_monsters(self) -> list[str]:
        """Return a list of monster slugs based on config filters and weighted selection."""

        def matches(mon: MonsterModel) -> bool:
            return (
                (not self._fish.stages or mon.stage.value in self._fish.stages)
                and (not self._fish.shapes or mon.shape in self._fish.shapes)
                and (
                    not self._fish.types
                    or any(t in self._fish.types for t in mon.types)
                )
                and (
                    not self._fish.tags
                    or any(tag in self._fish.tags for tag in mon.tags)
                )
            )

        filtered = [mon for mon in lookup_cache.values() if matches(mon)]

        if not filtered:
            logger.error(
                f"No monsters matched. Expected stage: {self._fish.stages}, shape: {self._fish.shapes}, "
                f"type: {self._fish.types}, tag: {self._fish.tags}"
            )
            return []

        weights = [self._compute_monster_weight(mon) for mon in filtered]
        return random.choices(
            [mon.slug for mon in filtered], weights=weights, k=1
        )

    def _compute_monster_weight(self, mon: MonsterModel) -> float:
        """Compute total weight for a monster based on config weight maps."""
        shape_weight = self._fish.shape_weights.get(mon.shape, 1.0)
        stage_weight = self._fish.stage_weights.get(mon.stage.value, 1.0)
        type_weight = max(
            [self._fish.type_weights.get(t, 1.0) for t in mon.types],
            default=1.0,
        )
        tag_weight = max(
            [self._fish.tag_shape.get(tag, 1.0) for tag in mon.tags],
            default=1.0,
        )
        return shape_weight * stage_weight * type_weight * tag_weight

    def _trigger_fishing_encounter(self, mon_slug: str, level: int) -> None:
        """Prepare a fishing encounter (store slug + level only)."""
        self._pending_encounter = (mon_slug, level)
        self._trigger_next_frame = True


def _lookup_monsters() -> None:
    global lookup_cache
    lookup_cache = {
        mon_name: result
        for mon_name in db.database["monster"]
        if (result := MonsterModel.lookup(mon_name, db)).txmn_id > 0
    }
