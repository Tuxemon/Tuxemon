# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from enum import Enum
from typing import TYPE_CHECKING

from tuxemon.db import StackingMode

if TYPE_CHECKING:
    from tuxemon.db import Modifier
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


def handle_type(modifier: Modifier, monster: Monster) -> float | None:
    if any(t.name in modifier.values for t in monster.types.current):
        return modifier.multiplier
    return None


def handle_tag(modifier: Modifier, monster: Monster) -> float | None:
    if any(t in modifier.values for t in monster.tags):
        return modifier.multiplier
    return None


def handle_terrain(modifier: Modifier, monster: Monster) -> float | None:
    if any(t in modifier.values for t in monster.terrains):
        return modifier.multiplier
    return None


def handle_shape(modifier: Modifier, monster: Monster) -> float | None:
    if any(t == monster.shape.slug for t in modifier.values):
        return modifier.multiplier
    return None


def handle_stage(modifier: Modifier, monster: Monster) -> float | None:
    if any(t == monster.stage.value for t in modifier.values):
        return modifier.multiplier
    return None


def handle_species(modifier: Modifier, monster: Monster) -> float | None:
    if any(t == monster.species for t in modifier.values):
        return modifier.multiplier
    return None


def handle_stat(modifier: Modifier, monster: Monster) -> float | None:
    logger.warning(
        "handle_stat() is a reserved placeholder for taste/terrain/weather modifiers. "
        "Do not use directly."
    )
    return None


def handle_stat_max(modifier: Modifier, monster: Monster) -> float | None:
    """
    Check if the modifier applies to the monster's highest base stat.
    """
    stats_dict = {
        name: getattr(monster.base_stats, name)
        for name in monster.base_stats.names()
    }
    highest_stat_name = max(stats_dict.keys(), key=lambda k: stats_dict[k])

    if highest_stat_name in modifier.values:
        return modifier.multiplier
    return None


def handle_stat_min(modifier: Modifier, monster: Monster) -> float | None:
    """
    Check if the modifier applies to the monster's lowest base stat.
    """
    stats_dict = {
        name: getattr(monster.base_stats, name)
        for name in monster.base_stats.names()
    }
    lowest_stat_name = min(stats_dict.keys(), key=lambda k: stats_dict[k])

    if lowest_stat_name in modifier.values:
        return modifier.multiplier
    return None


ATTRIBUTE_HANDLER_REGISTRY: dict[
    str, Callable[[Modifier, Monster], float | None]
] = {
    "type": handle_type,
    "tag": handle_tag,
    "terrain": handle_terrain,
    "shape": handle_shape,
    "stage": handle_stage,
    "species": handle_species,
    "stat": handle_stat,
    "stat_max": handle_stat_max,
    "stat_min": handle_stat_min,
}

CONDITION_REGISTRY: dict[str, Callable[[Monster], bool]] = {
    "hp_below_50": lambda m: m.hp_ratio < 0.5,
    "hp_above_50": lambda m: m.hp_ratio > 0.5,
    "full_hp": lambda m: m.hp_ratio == 1.0,
}


class ModifierMode(str, Enum):
    FIRST = "first"
    WEAKEST = "weakest"
    STRONGEST = "strongest"
    AVERAGE = "average"
    CUMULATIVE = "cumulative"


def parse_modifier_mode(value: str) -> ModifierMode:
    """Parses a string into a ModifierMode enum."""
    return ModifierMode(value)


class ModifiersHandler:
    def __init__(
        self,
        modifiers: list[Modifier] | None = None,
        attribute_handlers: None
        | (dict[str, Callable[[Modifier, Monster], float | None]]) = None,
    ) -> None:
        self._modifiers: dict[str, list[Modifier]] = {}
        self._attribute_handlers = (
            attribute_handlers or ATTRIBUTE_HANDLER_REGISTRY.copy()
        )

        for m in modifiers or []:
            self._modifiers.setdefault(m.attribute, []).append(m)

    def register_handler(
        self,
        attribute: str,
        handler: Callable[[Modifier, Monster], float | None],
    ) -> None:
        self._attribute_handlers[attribute] = handler

    def get_modifiers(self, attribute: str) -> list[Modifier]:
        return self._modifiers.get(attribute, [])

    def has_modifier(self, attribute: str) -> bool:
        return attribute in self._modifiers

    def update_modifier(
        self, attribute: str, values: Sequence[str], multiplier: float
    ) -> None:
        if attribute in self._modifiers:
            for m in self._modifiers[attribute]:
                m.values = list(values)
                m.multiplier = multiplier

    def remove_modifier(self, attribute: str) -> None:
        self._modifiers.pop(attribute, None)

    def add_modifier(self, modifier: Modifier) -> None:
        self._modifiers.setdefault(modifier.attribute, []).append(modifier)

    def list_modifiers(self) -> list[Modifier]:
        return [m for group in self._modifiers.values() for m in group]

    def __iter__(self) -> Iterator[Modifier]:
        return iter(self.list_modifiers())

    def _get_applicable_multiplier(
        self, modifier: Modifier, monster: Monster
    ) -> float | None:
        if modifier.condition_name:
            condition = CONDITION_REGISTRY.get(modifier.condition_name)
            if condition is None:
                logger.warning(
                    f"Unknown condition '{modifier.condition_name}'"
                )
                return None
            elif not condition(monster):
                return None

        if (
            modifier.turns_remaining is not None
            and modifier.turns_remaining <= 0
        ):
            return None

        handler = self._attribute_handlers.get(modifier.attribute)
        if handler:
            return handler(modifier, monster)

        logger.critical(
            f"Missing attribute handler for '{modifier.attribute}'. "
            "Modifier will be ignored."
        )
        return None

    def get_multiplier(
        self, monster: Monster, mode: ModifierMode = ModifierMode.WEAKEST
    ) -> float:
        applicable_modifiers: list[Modifier] = []

        for modifier_list in self._modifiers.values():
            for modifier in modifier_list:
                result = self._get_applicable_multiplier(modifier, monster)
                if result is not None:
                    applicable_modifiers.append(modifier)

        if not applicable_modifiers:
            return 1.0

        # Sort by priority descending
        applicable_modifiers.sort(key=lambda m: m.priority, reverse=True)

        # Enforce max_stacks constraint
        applicable_modifiers = enforce_max_stacks(applicable_modifiers)

        if mode == ModifierMode.FIRST:
            return applicable_modifiers[0].multiplier
        elif mode == ModifierMode.WEAKEST:
            return min(m.multiplier for m in applicable_modifiers)
        elif mode == ModifierMode.STRONGEST:
            return max(m.multiplier for m in applicable_modifiers)
        elif mode == ModifierMode.AVERAGE:
            return sum(m.multiplier for m in applicable_modifiers) / len(
                applicable_modifiers
            )
        elif mode == ModifierMode.CUMULATIVE:
            result = 1.0
            for m in applicable_modifiers:
                if m.stacking == StackingMode.ADDITIVE:
                    result += m.multiplier - 1.0
                elif m.stacking == StackingMode.MULTIPLICATIVE:
                    result *= m.multiplier
                elif m.stacking == StackingMode.OVERRIDE:
                    result = m.multiplier
                    break
            return result
        else:
            raise ValueError(f"Unknown modifier mode: {mode}")

    def weakest_link(self, monster: Monster) -> float:
        return self.get_multiplier(monster, ModifierMode.WEAKEST)

    def strongest_link(self, monster: Monster) -> float:
        return self.get_multiplier(monster, ModifierMode.STRONGEST)

    def cumulative_damage(self, monster: Monster) -> float:
        return self.get_multiplier(monster, ModifierMode.CUMULATIVE)

    def average_damage(self, monster: Monster) -> float:
        return self.get_multiplier(monster, ModifierMode.AVERAGE)

    def first_applicable_damage(self, monster: Monster) -> float:
        return self.get_multiplier(monster, ModifierMode.FIRST)

    def tick_turns(self) -> None:
        for modifier in self.list_modifiers():
            if modifier.turns_remaining is not None:
                modifier.turns_remaining -= 1

    def remove_expired_modifiers(self) -> None:
        for attr in list(self._modifiers):
            self._modifiers[attr] = [
                m
                for m in self._modifiers[attr]
                if m.turns_remaining is None or m.turns_remaining > 0
            ]
            if not self._modifiers[attr]:
                del self._modifiers[attr]


def enforce_max_stacks(modifiers: list[Modifier]) -> list[Modifier]:
    grouped = defaultdict(list)
    for m in modifiers:
        key = (m.attribute, tuple(sorted(m.values)))
        grouped[key].append(m)

    result = []
    for group in grouped.values():
        group.sort(key=lambda m: m.priority, reverse=True)
        max_stack = group[0].max_stacks
        if max_stack is not None:
            result.extend(group[:max_stack])
        else:
            result.extend(group)
    return result
