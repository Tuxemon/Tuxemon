# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Iterator, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tuxemon.db import Modifier
    from tuxemon.monster import Monster


class ModifierMode(str, Enum):
    FIRST = "first"
    WEAKEST = "weakest"
    STRONGEST = "strongest"
    AVERAGE = "average"
    CUMULATIVE = "cumulative"


def parse_modifier_mode(value: str) -> ModifierMode:
    """
    Parses a string into a ModifierMode enum.
    """
    return ModifierMode(value)


class ModifiersHandler:
    def __init__(self, modifiers: Optional[list[Modifier]] = None) -> None:
        self._modifiers: dict[str, list[Modifier]] = {}
        for m in modifiers or []:
            self._modifiers.setdefault(m.attribute, []).append(m)

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
    ) -> Optional[float]:
        if modifier.attribute == "type":
            if any(t.name in modifier.values for t in monster.types.current):
                return modifier.multiplier
        elif modifier.attribute == "tag":
            if any(t in modifier.values for t in monster.tags):
                return modifier.multiplier
        else:
            raise ValueError(f"{modifier.attribute} isn't implemented.")
        return None

    def get_multiplier(
        self, monster: Monster, mode: ModifierMode = ModifierMode.WEAKEST
    ) -> float:
        values = []
        for modifier_list in self._modifiers.values():
            for modifier in modifier_list:
                result = self._get_applicable_multiplier(modifier, monster)
                if result is not None:
                    values.append(result)

        if not values:
            return 1.0

        if mode == ModifierMode.FIRST:
            return values[0]
        elif mode == ModifierMode.WEAKEST:
            return min(values)
        elif mode == ModifierMode.STRONGEST:
            return max(values)
        elif mode == ModifierMode.AVERAGE:
            return sum(values) / len(values)
        elif mode == ModifierMode.CUMULATIVE:
            product = 1.0
            for v in values:
                product *= v
            return product
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
