# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any, Optional

from tuxemon.prepare import COEFF_STATS
from tuxemon.shape import ShapeHandler
from tuxemon.taste import Taste

logger = logging.getLogger(__name__)


@dataclass
class BasicStats:
    """The fundamental statistical attributes of a monster."""

    armour: int = 0
    dodge: int = 0
    hp: int = 0
    melee: int = 0
    ranged: int = 0
    speed: int = 0

    @classmethod
    def names(cls) -> list[str]:
        return [field.name for field in fields(cls)]

    def sum(self) -> int:
        total = sum(int(getattr(self, field.name)) for field in fields(self))
        return total

    def __add__(self, other: BasicStats) -> BasicStats:
        if not isinstance(other, BasicStats):
            return NotImplemented
        new_stats = BasicStats()
        for name in self.names():
            setattr(
                new_stats, name, getattr(self, name) + getattr(other, name)
            )
        return new_stats


@dataclass
class CustomStatBoosts(BasicStats):
    """
    Persistent, user- or modder-defined additive boosts to a monster's base
    stats.

    Unlike training points (which represent earned growth), custom stat boosts
    are external modifications that can be saved, loaded, and adjusted to
    tailor a monster's attributes beyond its natural progression.
    """

    def to_dict(self) -> Mapping[str, int]:
        return {
            field.name: getattr(self, field.name) for field in fields(self)
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> CustomStatBoosts:
        valid_fields = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class TrainingPoints(BasicStats):
    """Represents a monster's learned, trained potential."""

    def to_dict(self) -> Mapping[str, int]:
        return {
            field.name: getattr(self, field.name) for field in fields(self)
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> TrainingPoints:
        valid_fields = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class StatCalculator:

    def __init__(
        self,
        base_stats: BasicStats,
        level: int,
        shape: ShapeHandler,
        taste_cold: str,
        taste_warm: str,
        custom_stats: CustomStatBoosts,
        training_points: TrainingPoints,
    ):
        self.base_stats = base_stats
        self.level = level
        self.shape = shape
        self.taste_cold = taste_cold
        self.taste_warm = taste_warm
        self.custom_stats = custom_stats
        self.training_points = training_points

    def calculate(self) -> BasicStats:
        """Compute final stats from shape, level, taste, and modifiers."""
        raw_stats = self.calculate_raw_stats()
        cold = Taste.get_taste(self.taste_cold)
        warm = Taste.get_taste(self.taste_warm)
        final_stats = self.apply_stat_updates(raw_stats, cold, warm)
        return final_stats

    def calculate_raw_stats(self, level: Optional[int] = None) -> BasicStats:
        """Calculates stats before taste modifiers are applied."""
        level = level if level is not None else self.level
        stats = BasicStats()
        multiplier = level + COEFF_STATS
        level_scale = level / 100

        for stat in BasicStats.names():
            base_value = getattr(self.shape.attributes, stat) * multiplier
            raw_tp = getattr(self.training_points, stat)
            scaled_tp = int(raw_tp * level_scale)
            modifier = getattr(self.custom_stats, stat, 0)
            total = base_value + scaled_tp + modifier
            setattr(stats, stat, total)
        return stats

    def apply_stat_updates(
        self,
        stats: BasicStats,
        taste_cold: Optional[Taste],
        taste_warm: Optional[Taste],
    ) -> BasicStats:
        """Returns a new BasicStats object with taste modifiers applied."""
        updated = BasicStats()
        logger.debug("Applying taste-based stat updates")

        for attr in BasicStats.names():
            original_value = getattr(stats, attr)
            modified_value = self.update_stat(
                attr, original_value, taste_cold, taste_warm
            )
            logger.debug(f"{attr}: {original_value} → {modified_value}")
            setattr(updated, attr, modified_value)

        return updated

    def update_stat(
        self,
        stat_name: str,
        stat_value: int,
        taste_cold: Optional[Taste],
        taste_warm: Optional[Taste],
    ) -> int:
        """Applies taste modifiers to a single stat value."""
        modified_stat = float(stat_value)

        for taste in (taste_cold, taste_warm):
            if taste:
                for modifier in taste.modifiers:
                    if stat_name in modifier.values:
                        logger.debug(
                            f"Applying modifier {modifier.multiplier} to {stat_name} "
                            f"from taste {taste.slug}"
                        )
                        modified_stat *= modifier.multiplier

        return round(modified_stat)

    def calculate_at_level(self, target_level: int) -> BasicStats:
        """Returns final stats at a specific level without modifying internal state."""
        if target_level <= 0:
            raise ValueError("Target level must be a positive integer.")

        raw_stats = self.calculate_raw_stats(level=target_level)
        cold = Taste.get_taste(self.taste_cold)
        warm = Taste.get_taste(self.taste_warm)
        return self.apply_stat_updates(raw_stats, cold, warm)


class StatAnalyzer:
    """Provides detailed analysis, breakdown, and growth projections for monster stats."""

    def __init__(self, calculator: StatCalculator):
        self.calculator = calculator

    def get_breakdown(self) -> dict[str, dict[str, Any]]:
        """Returns a detailed breakdown of each stat's calculation."""
        breakdown = {}
        multiplier = self.calculator.level + COEFF_STATS
        level_scale = self.calculator.level / 100
        cold = Taste.get_taste(self.calculator.taste_cold)
        warm = Taste.get_taste(self.calculator.taste_warm)

        for stat_name in BasicStats.names():
            base_value = (
                getattr(self.calculator.shape.attributes, stat_name)
                * multiplier
            )
            raw_tp = getattr(self.calculator.training_points, stat_name)
            scaled_tp = int(raw_tp * level_scale)
            modifier_value = getattr(
                self.calculator.custom_stats, stat_name, 0
            )

            pre_taste_total = base_value + scaled_tp + modifier_value

            taste_multiplier = 1.0
            for taste in (cold, warm):
                if taste:
                    for modifier in taste.modifiers:
                        if stat_name in modifier.values:
                            taste_multiplier *= modifier.multiplier

            final_value = round(pre_taste_total * taste_multiplier)

            breakdown[stat_name] = {
                "base_value": int(base_value),
                "training_points_raw": raw_tp,
                "training_points_scaled": scaled_tp,
                "temporary_modifier": modifier_value,
                "pre_taste_total": int(pre_taste_total),
                "taste_multiplier": taste_multiplier,
                "final_value": final_value,
            }
        return breakdown

    def evaluate_taste_efficiency(self) -> float:
        """Returns a normalized synergy score (-1 to +1) based on taste effects."""
        breakdown = self.get_breakdown()
        score: float = 0.0
        total_base: float = 0.0

        for stat_name, data in breakdown.items():
            base_stat_value = getattr(
                self.calculator.shape.attributes, stat_name
            )
            total_base += base_stat_value

            if data["taste_multiplier"] > 1.0:
                score += base_stat_value * (data["taste_multiplier"] - 1.0)
            elif data["taste_multiplier"] < 1.0:
                score -= base_stat_value * (1.0 - data["taste_multiplier"])

        # Normalize to [-1, +1] range
        if total_base > 0:
            normalized_score = score / total_base
        else:
            normalized_score = 0.0

        return normalized_score

    def get_stat_growth_curve(self, max_level: int) -> dict[int, BasicStats]:
        """Returns a level-to-stats map showing progression up to max_level."""
        if max_level <= 0:
            raise ValueError("max_level must be a positive integer.")

        growth_curve = {}
        for level in range(1, max_level + 1):
            growth_curve[level] = self.calculator.calculate_at_level(level)

        return growth_curve


def randomize_stats(min_val: int, max_val: int) -> BasicStats:
    """Generates a BasicStats object with random values within a range."""
    if min_val > max_val:
        raise ValueError("min_val cannot be greater than max_val")

    random_stats = BasicStats()
    for name in BasicStats.names():
        setattr(random_stats, name, random.randint(min_val, max_val))
    return random_stats


def randomize_training_points(total_points: int) -> TrainingPoints:
    """Generates randomized training points that sum to a specified total."""
    if total_points < 0:
        raise ValueError("Total points cannot be negative.")

    stats = TrainingPoints()
    stat_names = BasicStats.names()
    num_stats = len(stat_names)
    remaining_points = total_points

    for i in range(num_stats - 1):
        max_possible = remaining_points // (num_stats - i)
        points = random.randint(0, max_possible)
        setattr(stats, stat_names[i], points)
        remaining_points -= points

    setattr(stats, stat_names[-1], remaining_points)
    return stats


def compare_stats(
    before: BasicStats, after: BasicStats
) -> dict[str, tuple[int, int, int]]:
    """
    Compare two BasicStats objects and return a dict of stat differences.
    Each entry is a tuple: (before, after, delta)
    """
    comparison = {}
    for name in BasicStats.names():
        old = getattr(before, name)
        new = getattr(after, name)
        delta = new - old
        logger.debug(f"Comparing {name}: {old} → {new} (Δ {delta})")
        comparison[name] = (old, new, delta)
    return comparison
