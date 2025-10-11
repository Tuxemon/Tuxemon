# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from tuxemon.constants import paths
from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import MonsterModel, db

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

lookup_cache: dict[str, MonsterModel] = {}


@dataclass
class ActionConfig:
    trigger: float = 0.0
    lower_bound: int = 0
    upper_bound: int = 0
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
    exp_req_mod: list[float] = field(default_factory=list)

    def validate_parameters(self) -> None:
        if not (0 <= self.trigger <= 1):
            raise ValueError("Trigger must be between 0 and 1 inclusive.")
        if self.lower_bound < 0 or self.upper_bound < 0:
            raise ValueError("Bounds must be non-negative.")
        if self.lower_bound > self.upper_bound:
            raise ValueError("Lower bound cannot exceed upper bound.")


def load_yaml(filepath: Path) -> Any:
    try:
        with filepath.open() as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


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


@dataclass
class FishingEffect(CoreEffect):
    """This effect triggers fishing."""

    name = "fishing"

    def apply_item(self, session: Session, item: Item) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_monsters()

        self.player = session.player
        self.client = session.client
        fishing_configs = Loader.get_config_fishing(f"{self.name}.yaml")

        self._fish: ActionConfig = fishing_configs[item.slug]
        self._fish.validate_parameters()

        monster_slugs = self._get_fishing_monsters()

        if monster_slugs and random.random() <= self._fish.trigger:
            mon_slug = monster_slugs[0]
            level = random.randint(
                self._fish.lower_bound, self._fish.upper_bound
            )
            self._trigger_fishing_encounter(mon_slug, level)
            return ItemEffectResult(name=item.name, success=True)

        return ItemEffectResult(name=item.name)

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
        """Trigger a fishing encounter with environment, color, held item, and exp modifier."""
        environment = (
            self._fish.environment.get("night")
            if self.player.game_variables.get("stage_of_day") == "night"
            else self._fish.environment.get("default")
        )

        rgb = ":".join(map(str, self._fish.animation_color))

        held_item = None
        if self._fish.held_items:
            items, weights = zip(*self._fish.held_items.items())
            held_item = random.choices(items, weights=weights, k=1)[0]

        logger.debug(
            f"Selected monster: {mon_slug}, level: {level}, held_item: {held_item}"
        )

        exp_req_mod = self._fish.exp_req_mod

        self.client.event_engine.execute_action(
            "wild_encounter",
            [mon_slug, level, exp_req_mod, None, environment, rgb, held_item],
            True,
        )


def _lookup_monsters() -> None:
    global lookup_cache
    lookup_cache = {
        mon_name: result
        for mon_name in db.database["monster"]
        if (result := MonsterModel.lookup(mon_name, db)).txmn_id > 0
    }
