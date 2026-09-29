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


@dataclass
class TrapConfig:
    expire_time: float | None = None
    max_distance: int | None = None
    trigger_chance: float | None = None
    failure_dialog: str = "trap_failed"
    success_dialog: str = "trap_triggered"
    level_bounds: tuple[int, int] = (0, 0)
    weight_bounds: tuple[float, float] | None = None
    stages: list[str] = field(default_factory=list)
    stage_weights: dict[str, float] = field(default_factory=dict)
    shapes: list[str] = field(default_factory=list)
    shape_weights: dict[str, float] = field(default_factory=dict)
    types: list[str] = field(default_factory=list)
    type_weights: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    tag_weights: dict[str, float] = field(default_factory=dict)

    def validate_parameters(self) -> None:
        if self.expire_time and self.expire_time < 0:
            raise ValueError("Expire time must be non-negative.")
        if self.max_distance and self.max_distance < 0:
            raise ValueError("Max distance must be non-negative.")
        if self.trigger_chance and not (0 <= self.trigger_chance <= 1):
            raise ValueError("Trigger chance must be between 0 and 1.")
        if self.level_bounds[0] < 0 or self.level_bounds[1] < 0:
            raise ValueError("Bounds must be non-negative.")
        if self.level_bounds[0] > self.level_bounds[1]:
            raise ValueError("Lower bound cannot exceed upper bound.")
        if self.weight_bounds:
            low, high = self.weight_bounds
            if low < 0 or high < 0:
                raise ValueError("Weight bounds must be non-negative.")
            if low > high:
                raise ValueError(
                    "Lower weight bound cannot exceed upper bound."
                )


class Loader:
    _config_trap: dict[str, TrapConfig] = {}

    @classmethod
    def get_config_trap(cls, filename: str) -> dict[str, TrapConfig]:
        yaml_path = paths.mods_folder / filename
        if not cls._config_trap:
            raw_map = load_yaml(yaml_path)
            cls._config_trap = {
                key: TrapConfig(**item) for key, item in raw_map.items()
            }
        return cls._config_trap


class TrapStage(Enum):
    SETUP = 1
    ARMED = 2
    TRIGGERED = 3
    RESOLVE = 4
    DONE = 5


@dataclass
class TrapEffect(CoreEffect):
    """
    Applies the "trap" effect to an item.

    This effect simulates setting a trap in the overworld. A trap progresses
    through multiple stages (setup, armed, triggered, resolve, done) and may
    expire if conditions are not met. When triggered, the trap can initiate
    a wild monster encounter based on configurable parameters.

    **Stages**
    - ``SETUP`` → Trap is placed and initializing.
    - ``ARMED`` → Trap is active and waiting for conditions.
    - ``TRIGGERED`` → Trap has been activated.
    - ``RESOLVE`` → Trap resolves its outcome (encounter or failure).
    - ``DONE`` → Trap is finished and no longer active.

    **Parameters (from TrapConfig)**
    - ``expire_time``: Float, maximum time before trap expires.
    - ``max_distance``: Integer, maximum distance player can move before trap expires.
    - ``trigger_chance``: Float (0–1), probability of trap triggering.
    - ``failure_dialog``: String, dialog key shown if trap fails.
    - ``success_dialog``: String, dialog key shown if trap succeeds.
    - ``level_bounds``: Tuple[int, int], min and max monster level for encounters.
    - ``weight_bounds``: Optional tuple[float, float], min and max monster weight.
    - ``stages``: List of allowed monster stages.
    - ``shapes``: List of allowed monster shapes.
    - ``types``: List of allowed monster types.
    - ``tags``: List of allowed monster tags.
    - ``*_weights``: Dicts providing weighting factors for stage, shape, type, and tag.

    **Example**

    .. code-block:: json

        "effects": [
            "trap"
        ]
    """

    name = "trap"
    stage: TrapStage = TrapStage.SETUP
    _elapsed: float = 0.0
    _duration: float = 0.0
    _finished: bool = False
    _pending_encounter: tuple[str, int] | None = None

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        MonsterModel.load_cache(db)
        self.cache = MonsterModel.get_cache()
        trap_configs = Loader.get_config_trap("trap.yaml")
        self._trap: TrapConfig = trap_configs[item.slug]
        self._trap.validate_parameters()

        self.stage = TrapStage.SETUP
        self._elapsed = 0.0
        self._duration = 1.0
        self._origin_map = session.player.current_map
        self._origin_pos = session.player.tile_pos
        return ItemEffectResult(name=item.name, success=True)

    def update(self, session: Session, dt: float) -> None:
        self._elapsed += dt

        if self.stage == TrapStage.SETUP and self._elapsed >= self._duration:
            self.stage = TrapStage.ARMED
            self._elapsed = 0.0

        elif self.stage == TrapStage.ARMED:
            if session.player.current_map != self._origin_map:
                self._expire(session)
            elif self._trap.max_distance and (
                self._distance(session.player.tile_pos, self._origin_pos)
                > self._trap.max_distance
            ):
                self._expire(session)
            elif (
                self._trap.expire_time
                and self._elapsed >= self._trap.expire_time
            ):
                self._expire(session)
            else:
                self.trigger()

        elif self.stage == TrapStage.TRIGGERED:
            self.stage = TrapStage.RESOLVE
            self._elapsed = 0.0
            self._duration = 0.5

        elif (
            self.stage == TrapStage.RESOLVE and self._elapsed >= self._duration
        ):
            if self._pending_encounter:
                mon_slug, level = self._pending_encounter
                session.client.event_engine.execute_action(
                    "wild_encounter",
                    [mon_slug, level, None, None, None, None],
                    True,
                )
                session.client.event_engine.execute_action(
                    "translated_dialog", [self._trap.success_dialog], True
                )
            else:
                session.client.event_engine.execute_action(
                    "translated_dialog", [self._trap.failure_dialog], True
                )
            self.stage = TrapStage.DONE
            self._finished = True

    def trigger(self) -> None:
        if (
            self._trap.trigger_chance
            and random.random() <= self._trap.trigger_chance
        ):
            mon_slug = self._get_trap_monsters()[0]
            low, high = self._trap.level_bounds
            level = random.randint(low, high)
            self._pending_encounter = (mon_slug, level)
            self.stage = TrapStage.TRIGGERED
        else:
            self._pending_encounter = None

    def cancel(self, session: Session) -> None:
        self._expire(session)

    def _expire(self, session: Session) -> None:
        session.client.event_engine.execute_action(
            "translated_dialog", ["trap_expired"], True
        )
        self.stage = TrapStage.DONE
        self._finished = True

    def _distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def is_finished(self) -> bool:
        return self._finished

    def _get_trap_monsters(self) -> list[str]:
        def matches(mon: MonsterModel) -> bool:
            return (
                (not self._trap.stages or mon.stage.value in self._trap.stages)
                and (not self._trap.shapes or mon.shape in self._trap.shapes)
                and (
                    not self._trap.types
                    or any(t in self._trap.types for t in mon.types)
                )
                and (
                    not self._trap.tags
                    or any(tag in self._trap.tags for tag in mon.tags)
                )
                and (
                    not self._trap.weight_bounds
                    or (
                        self._trap.weight_bounds[0]
                        <= mon.weight
                        <= self._trap.weight_bounds[1]
                    )
                )
            )

        filtered = [mon for mon in self.cache.values() if matches(mon)]
        if not filtered:
            logger.error("No monsters matched trap filters")
            return []

        weights = [self._compute_monster_weight(mon) for mon in filtered]
        return random.choices(
            [mon.slug for mon in filtered], weights=weights, k=1
        )

    def _compute_monster_weight(self, mon: MonsterModel) -> float:
        shape_weight = self._trap.shape_weights.get(mon.shape, 1.0)
        stage_weight = self._trap.stage_weights.get(mon.stage.value, 1.0)
        type_weight = max(
            [self._trap.type_weights.get(t, 1.0) for t in mon.types],
            default=1.0,
        )
        tag_weight = max(
            [self._trap.tag_weights.get(tag, 1.0) for tag in mon.tags],
            default=1.0,
        )
        return shape_weight * stage_weight * type_weight * tag_weight
