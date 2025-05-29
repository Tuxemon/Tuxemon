# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import yaml

from tuxemon.constants import paths
from tuxemon.core.core_effect import ItemEffect, ItemEffectResult
from tuxemon.db import MonsterModel, db

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

lookup_cache: dict[str, MonsterModel] = {}


@dataclass
class FishingConfig:
    bait: float
    lower_bound: int
    upper_bound: int
    stage: list[str]
    shape: list[str]
    shape_weights: dict[str, float]
    sea_blue_color: list[int]
    environment: dict[str, str]
    held_items: list[str]
    exp_req_mod: list[float]

    def validate_parameters(self) -> None:
        if not (0 <= self.bait <= 1):
            raise ValueError("Bait must be between 0 and 1 inclusive.")
        if self.lower_bound < 0:
            raise ValueError("Lower bound must be non-negative.")
        if self.upper_bound < 0:
            raise ValueError("Upper bound must be non-negative.")
        if self.lower_bound > self.upper_bound:
            raise ValueError("Lower bound cannot be greater than upper bound.")


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
    _config_fishing: dict[str, FishingConfig] = {}

    @classmethod
    def get_config_fishing(cls, filename: str) -> dict[str, FishingConfig]:
        yaml_path = paths.mods_folder / filename
        if not cls._config_fishing:
            raw_map = load_yaml(yaml_path)
            cls._config_fishing = {
                key: FishingConfig(**item) for key, item in raw_map.items()
            }
        return cls._config_fishing


@dataclass
class FishingEffect(ItemEffect):
    """This effect triggers fishing."""

    name = "fishing"

    def apply(
        self, session: Session, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_monsters()

        self.player = session.player
        self.client = session.client
        fishing_configs = Loader.get_config_fishing(f"{self.name}.yaml")

        self._fish: FishingConfig = fishing_configs[item.slug]
        self._fish.validate_parameters()

        monster_lists = self._get_fishing_monsters()

        if monster_lists and random.random() <= self._fish.bait:
            mon_slug = random.choice(monster_lists)
            level = random.randint(
                self._fish.lower_bound, self._fish.upper_bound
            )
            self._trigger_fishing_encounter(mon_slug, level)
            return ItemEffectResult(name=item.name, success=True)
        return ItemEffectResult(name=item.name)

    def _get_fishing_monsters(self) -> list[str]:
        """Return a list of monster slugs based on config and shapes with logging for errors."""
        monsters = [
            mon.slug
            for mon in lookup_cache.values()
            if mon.stage.value in self._fish.stage
            and mon.shape in self._fish.shape
        ]

        if not monsters:
            logger.error(
                f" Expected shapes: {self._fish.shape}, but none matched."
            )

        weights = [self._fish.shape_weights.get(mon, 1.0) for mon in monsters]
        if not monsters:
            return []
        else:
            return random.choices(monsters, weights=weights, k=1)

    def _trigger_fishing_encounter(self, mon_slug: str, level: int) -> None:
        """Trigger a fishing encounter"""

        environment = (
            self._fish.environment.get("night")
            if self.player.game_variables["stage_of_day"] == "night"
            else self._fish.environment.get("default")
        )
        rgb = ":".join(map(str, self._fish.sea_blue_color))
        held_item = (
            random.choice(self._fish.held_items)
            if self._fish.held_items
            else None
        )
        exp_req_mod = self._fish.exp_req_mod
        self.client.event_engine.execute_action(
            "wild_encounter",
            [mon_slug, level, exp_req_mod, None, environment, rgb, held_item],
            True,
        )


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results
