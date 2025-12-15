# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


class PartyStats:
    """Provides statistical calculations for a list of Monster objects."""

    @staticmethod
    def alive(monsters: list[Monster]) -> list[Monster]:
        return [m for m in monsters if not m.is_fainted]

    @staticmethod
    def is_fainted(monsters: list[Monster]) -> bool:
        return all(m.is_fainted for m in monsters)

    @staticmethod
    def no_tech(monsters: list[Monster]) -> list[str]:
        return [m.name for m in monsters if not m.moves.has_moves()]

    @staticmethod
    def calculate_level_lowest(monsters: list[Monster]) -> Optional[int]:
        """Returns the lowest level, or None if the list is empty."""
        if not monsters:
            return None
        return min(mon.level for mon in monsters)

    @staticmethod
    def calculate_level_highest(monsters: list[Monster]) -> Optional[int]:
        """Returns the highest level, or None if the list is empty."""
        if not monsters:
            return None
        return max(mon.level for mon in monsters)

    @staticmethod
    def calculate_level_average(monsters: list[Monster]) -> Optional[int]:
        """Returns the average level, or None if the list is empty."""
        if not monsters:
            return None
        total = sum(mon.level for mon in monsters)
        return round(total / len(monsters))

    @staticmethod
    def get_alignment(monsters: list[Monster]) -> Optional[str]:
        """
        Returns the dominant elemental type in the list,
        based on the most frequently occurring type.
        """
        type_counter: Counter[str] = Counter()

        for monster in monsters:
            try:
                type_slugs = monster.types.get_type_slugs()
                type_counter.update(type_slugs)
            except Exception:
                continue

        if not type_counter:
            return None

        dominant_type, _ = type_counter.most_common(1)[0]
        return dominant_type

    @staticmethod
    def has_type(monsters: list[Monster], element_slug: str) -> bool:
        """Returns True if any monster has the given type."""
        return any(mon.has_type(element_slug) for mon in monsters)

    @staticmethod
    def has_tech(monsters: list[Monster], tech_slug: str) -> bool:
        """Returns True if any monster has the given technique."""
        for monster in monsters:
            if monster.moves.has_move(tech_slug):
                return True
        return False
