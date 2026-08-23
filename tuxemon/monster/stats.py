# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Mapping
from dataclasses import astuple, dataclass, field, fields, replace
from typing import TYPE_CHECKING, Any

from tuxemon.database.rules import config_monster
from tuxemon.taste import Taste

if TYPE_CHECKING:
    from tuxemon.shape import ShapeHandler

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
        return sum(astuple(self))

    def to_dict(self) -> Mapping[str, int]:
        return {
            field.name: getattr(self, field.name) for field in fields(self)
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> BasicStats:
        valid_fields = {field.name for field in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})

    def copy(self) -> BasicStats:
        return replace(self)

    def __add__(self, other: BasicStats) -> BasicStats:
        if not isinstance(other, BasicStats):
            return NotImplemented
        return self.__class__(
            *[s + o for s, o in zip(astuple(self), astuple(other))]
        )

    def __iadd__(self, other: BasicStats) -> BasicStats:
        if not isinstance(other, BasicStats):
            return NotImplemented
        for f in fields(self):
            setattr(
                self, f.name, getattr(self, f.name) + getattr(other, f.name)
            )
        return self


NONLINEAR_TABLE = {
    -6: 2 / 8,
    -5: 2 / 7,
    -4: 2 / 6,
    -3: 2 / 5,
    -2: 2 / 4,
    -1: 2 / 3,
    0: 1.0,
    1: 3 / 2,
    2: 4 / 2,
    3: 5 / 2,
    4: 6 / 2,
    5: 7 / 2,
    6: 8 / 2,
}

MIN_STAGE = min(NONLINEAR_TABLE)
MAX_STAGE = max(NONLINEAR_TABLE)

DEFAULT_SCALING_MODE = "nonlinear"
DEFAULT_STEP_LIMIT = MAX_STAGE


def stage_multiplier(
    stage: int, scaling_mode: str, max_step_limit: int
) -> float:
    """The multiplier a cumulative step stage applies to a base stat."""
    if scaling_mode == "linear":
        if max_step_limit <= 0:
            return 1.0
        return 1 + (stage / max_step_limit)
    return NONLINEAR_TABLE[max(MIN_STAGE, min(MAX_STAGE, int(stage)))]


@dataclass
class StatStage:
    """
    The cumulative step stage on a single stat.

    One stage per stat, shared by every source that raises or lowers it,
    so +2 steps from an item on top of +2 from a status is one +4 stage
    rather than two multipliers stacked on each other.
    """

    stage: int = 0
    scaling_mode: str = DEFAULT_SCALING_MODE
    max_step_limit: int = DEFAULT_STEP_LIMIT

    def multiplier(self) -> float:
        return stage_multiplier(
            self.stage, self.scaling_mode, self.max_step_limit
        )

    def clamp(self, stage: int) -> int:
        limit = max(0, self.max_step_limit)
        return max(-limit, min(limit, stage))


@dataclass
class StatContribution:
    """What one source contributed, so it can be taken back when it ends."""

    stages: dict[str, int] = field(default_factory=dict)
    flat: BasicStats = field(default_factory=BasicStats)

    def is_empty(self) -> bool:
        return not any(self.stages.values()) and not any(astuple(self.flat))


class TemporaryStatBoosts:
    """
    Combat-only stat modifications recorded against a monster.

    The boosts are owned by the monster they affect, not by whatever
    applied them, so an item used from the bag counts exactly like a
    status or a technique.

    Two kinds of modification are tracked. Step-based ones move the
    monster's stage for that stat, which every source shares. Value-based
    ones are flat additions, summed as they come.

    Each source's contribution is remembered as well, so that a source
    ending (a status expiring, say) takes back exactly what it granted
    and leaves everything else standing.

    Boosts are derived from the monster's base stats on read rather than
    frozen when applied, so they follow the monster if its base stats
    change mid-battle.

    Nothing here is persisted: boosts last for a battle only and are
    dropped by ``Monster.clear_all_temporary_boosts``.
    """

    def __init__(self) -> None:
        self._stages: dict[str, StatStage] = {}
        self._flat = BasicStats()
        self._contributions: dict[str, StatContribution] = {}

    @staticmethod
    def _validate_stat(stat: str) -> None:
        if stat not in BasicStats.names():
            raise ValueError(f"Invalid stat name: {stat}")

    def _contribution(self, source_key: str) -> StatContribution:
        return self._contributions.setdefault(source_key, StatContribution())

    def get_stage(self, stat: str) -> int:
        """Returns the monster's cumulative step stage for a stat."""
        self._validate_stat(stat)
        state = self._stages.get(stat)
        return state.stage if state else 0

    def add_stage(
        self,
        source_key: str,
        stat: str,
        delta: int,
        scaling_mode: str = DEFAULT_SCALING_MODE,
        max_step_limit: int = DEFAULT_STEP_LIMIT,
    ) -> int:
        """
        Moves the monster's stage for a stat, clamped to the step limit.

        Returns the new stage. What the step limit actually allowed is
        credited to the source, so a stage granted at the cap gives back
        only as much as it took.
        """
        self._validate_stat(stat)
        state = self._stages.setdefault(stat, StatStage())
        state.scaling_mode = scaling_mode
        state.max_step_limit = max(0, int(max_step_limit))

        previous = state.stage
        state.stage = state.clamp(previous + int(delta))
        applied = state.stage - previous

        contribution = self._contribution(source_key)
        contribution.stages[stat] = contribution.stages.get(stat, 0) + applied
        return state.stage

    def get_flat(self, stat: str) -> int:
        """Returns the flat, value-based addition to a stat."""
        self._validate_stat(stat)
        return int(getattr(self._flat, stat))

    def add_flat(self, source_key: str, stat: str, value: int) -> None:
        """Adds a flat, value-based boost to a stat."""
        self._validate_stat(stat)
        setattr(self._flat, stat, getattr(self._flat, stat) + int(value))
        contribution = self._contribution(source_key)
        setattr(
            contribution.flat,
            stat,
            getattr(contribution.flat, stat) + int(value),
        )

    def total(self, base_stats: BasicStats) -> BasicStats:
        """
        The boost to add to each stat, given the monster's base stats.

        A stat is never pushed below 1, matching what a single
        modification is allowed to do on its own.
        """
        total = BasicStats()
        for stat in BasicStats.names():
            base = getattr(base_stats, stat)
            state = self._stages.get(stat)

            boost = int(base * state.multiplier()) - base if state else 0
            boost += getattr(self._flat, stat)

            if boost < 0:
                boost = max(boost, 1 - base)

            setattr(total, stat, boost)
        return total

    def withdraw(self, source_key: str) -> None:
        """Takes back everything one source contributed."""
        contribution = self._contributions.pop(source_key, None)
        if contribution is None:
            return

        for stat, applied in contribution.stages.items():
            state = self._stages.get(stat)
            if state:
                state.stage = state.clamp(state.stage - applied)

        for stat in BasicStats.names():
            value = getattr(contribution.flat, stat)
            if value:
                setattr(self._flat, stat, getattr(self._flat, stat) - value)

    def clear(self) -> None:
        """Drops every temporary boost."""
        self._stages.clear()
        self._flat = BasicStats()
        self._contributions.clear()

    def is_empty(self) -> bool:
        return not any(
            state.stage for state in self._stages.values()
        ) and not any(astuple(self._flat))

    def __repr__(self) -> str:
        stages = {
            stat: state.stage
            for stat, state in self._stages.items()
            if state.stage
        }
        return f"<TemporaryStatBoosts stages={stages} flat={self._flat}>"


@dataclass
class IndividualValues(BasicStats):
    """
    Inherent, unchangeable statistical potential assigned upon a monster's
    creation, typically ranging from 0 to 31 for each stat.
    """

    def to_dict(self) -> Mapping[str, int]:
        return {
            field.name: getattr(self, field.name) for field in fields(self)
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> IndividualValues:
        valid_fields = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


def randomize_ivs() -> IndividualValues:
    """
    Generates Individual Values (IVs) for all stats
    """
    min_iv, max_iv = config_monster.iv_range
    random_data = {
        name: random.randint(min_iv, max_iv) for name in BasicStats.names()
    }
    return IndividualValues(**random_data)


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

    def get_contribution(self, level: int) -> BasicStats:
        """Returns the floor-level scaled contribution of TPs."""
        contribution = BasicStats()
        level_scale = level / 100
        for name in self.names():
            raw_tp = getattr(self, name)
            setattr(contribution, name, int(raw_tp * level_scale))
        return contribution

    def set_stat(self, stat_name: str, value: int) -> None:
        if not hasattr(self, stat_name):
            raise ValueError(f"Invalid stat name: {stat_name}")
        setattr(self, stat_name, value)

    def validate(self) -> None:
        """Clamps individual stats and the total to configuration limits."""
        max_stat = config_monster.max_tps
        max_total = config_monster.max_total_tps

        # Clamp individual stats
        for name in self.names():
            val = getattr(self, name)
            if val > max_stat:
                setattr(self, name, max_stat)

        # Clamp total if needed (proportional scaling)
        current_total = self.sum()
        if current_total > max_total:
            ratio = max_total / current_total
            for name in self.names():
                setattr(self, name, int(getattr(self, name) * ratio))
            logger.warning(f"TPs exceeded {max_total} and were scaled down.")


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
        individual_values: IndividualValues,
    ):
        self.base_stats = base_stats
        self.level = level
        self.shape = shape
        self.taste_cold = taste_cold
        self.taste_warm = taste_warm
        self.custom_stats = custom_stats
        self.training_points = training_points
        self.individual_values = individual_values

    def calculate(
        self, temporary_boosts: BasicStats | None = None
    ) -> BasicStats:
        """Compute final stats from shape, level, taste, and modifiers."""
        raw_stats = self.calculate_raw_stats()
        cold = Taste.get(self.taste_cold)
        warm = Taste.get(self.taste_warm)
        final_stats = self.apply_stat_updates(raw_stats, cold, warm)

        if temporary_boosts:
            final_stats += temporary_boosts

        return final_stats

    def calculate_raw_stats(self, level: int | None = None) -> BasicStats:
        """Calculates stats before taste modifiers are applied."""
        level = level if level is not None else self.level
        multiplier = level + config_monster.coeff_stats
        tp_contribution = self.training_points.get_contribution(level)

        stats_dict = {}
        for stat in BasicStats.names():
            base = getattr(self.shape.attributes, stat) * multiplier
            iv = getattr(self.individual_values, stat, 0)
            tp = getattr(tp_contribution, stat)
            mod = getattr(self.custom_stats, stat, 0)
            stats_dict[stat] = int(base + iv + tp + mod)

        return BasicStats(**stats_dict)

    def apply_stat_updates(
        self,
        stats: BasicStats,
        taste_cold: Taste | None,
        taste_warm: Taste | None,
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
        taste_cold: Taste | None,
        taste_warm: Taste | None,
    ) -> int:
        """Applies taste modifiers to a single stat value."""
        modified = stat_value
        for taste in (taste_cold, taste_warm):
            if taste:
                modified = taste.apply_to_stat(stat_name, modified)
        return modified

    def calculate_at_level(self, target_level: int) -> BasicStats:
        """Returns final stats at a specific level without modifying internal state."""
        if target_level <= 0:
            raise ValueError("Target level must be a positive integer.")

        raw_stats = self.calculate_raw_stats(level=target_level)
        cold = Taste.get(self.taste_cold)
        warm = Taste.get(self.taste_warm)
        return self.apply_stat_updates(raw_stats, cold, warm)


class StatAnalyzer:
    """Provides detailed analysis, breakdown, and growth projections for monster stats."""

    def __init__(self, calculator: StatCalculator):
        self.calculator = calculator

    def get_breakdown(self) -> dict[str, dict[str, Any]]:
        """Returns a detailed breakdown of each stat's calculation."""
        breakdown = {}
        level = self.calculator.level
        multiplier = level + config_monster.coeff_stats

        # Use the new TP scaling logic
        tp_contribution = self.calculator.training_points.get_contribution(
            level
        )

        cold = Taste.get(self.calculator.taste_cold)
        warm = Taste.get(self.calculator.taste_warm)

        for stat_name in BasicStats.names():
            # Base from shape
            base_part = (
                getattr(self.calculator.shape.attributes, stat_name)
                * multiplier
            )

            # IVs
            iv_part = getattr(self.calculator.individual_values, stat_name, 0)

            # Scaled TPs (already floor-scaled)
            tp_part = getattr(tp_contribution, stat_name)

            # Custom stat boosts
            mod_part = getattr(self.calculator.custom_stats, stat_name, 0)

            # Pre‑taste total
            pre_taste_total = base_part + iv_part + tp_part + mod_part

            # Taste multiplier
            taste_multiplier = 1.0
            for taste in (cold, warm):
                if taste:
                    taste_multiplier *= taste.get_multiplier(stat_name)

            final_value = round(pre_taste_total * taste_multiplier)

            breakdown[stat_name] = {
                "base_value": int(base_part),
                "individual_value": iv_part,
                "training_points_raw": getattr(
                    self.calculator.training_points, stat_name
                ),
                "training_points_scaled": tp_part,
                "temporary_modifier": mod_part,
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
    max_per_stat = config_monster.max_tps
    remaining = total_points
    for name in stat_names[:-1]:
        cap = min(max_per_stat, remaining // len(stat_names))
        points = random.randint(0, cap)
        setattr(stats, name, points)
        remaining -= points
    setattr(stats, stat_names[-1], min(remaining, max_per_stat))
    stats.validate()
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
