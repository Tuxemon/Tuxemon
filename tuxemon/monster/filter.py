# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


def or_monster_filter(
    *filters: Callable[[Monster], bool],
) -> Callable[[Monster], bool]:
    return lambda monster: any(f(monster) for f in filters)


def and_monster_filter(
    *filters: Callable[[Monster], bool],
) -> Callable[[Monster], bool]:
    return lambda monster: all(f(monster) for f in filters)


def not_monster_filter(
    filter_func: Callable[[Monster], bool],
) -> Callable[[Monster], bool]:
    return lambda monster: not filter_func(monster)


class MonsterFilter:
    def __init__(self) -> None:
        self._filters: list[Callable[[Monster], bool]] = []

    def clear_filters(self) -> None:
        """Remove all applied filters."""
        self._filters.clear()

    def add_filter(self, filter_func: Callable[[Monster], bool]) -> None:
        """Add a single filter to the filter stack."""
        self._filters.append(filter_func)

    def set_filter_custom_or(
        self, *filter_funcs: Callable[[Monster], bool]
    ) -> None:
        """Set filters with logical OR — any condition passes."""
        self.clear_filters()
        self.add_filter(or_monster_filter(*filter_funcs))

    def set_filter_custom_and(
        self, *filter_funcs: Callable[[Monster], bool]
    ) -> None:
        """Set filters with logical AND — all conditions must pass."""
        self.clear_filters()
        self.add_filter(and_monster_filter(*filter_funcs))

    def set_filter_custom_not(
        self, filter_func: Callable[[Monster], bool]
    ) -> None:
        """Exclude monsters matching the given condition."""
        self.clear_filters()
        self.add_filter(not_monster_filter(filter_func))

    def filter_by_type(self, type_name: str) -> None:
        self.clear_filters()
        self.add_filter(
            lambda monster: any(
                m.slug == type_name for m in monster.types.current
            )
        )

    def filter_by_status(self, status_slug: str) -> None:
        self.clear_filters()
        self.add_filter(
            lambda monster: (
                (status := monster.status.current_status) is not None
                and status.slug == status_slug
            )
        )

    def filter_fainted(self) -> None:
        self.clear_filters()
        self.add_filter(lambda m: m.is_fainted)

    def filter_active(self) -> None:
        self.clear_filters()
        self.add_filter(lambda m: not m.is_fainted)

    def get_filtered_monsters(self, monsters: list[Monster]) -> list[Monster]:
        """Return only monsters that satisfy all filters."""
        if not self._filters:
            return monsters

        filtered = [m for m in monsters if all(f(m) for f in self._filters)]

        if not filtered:
            active_filters = [
                f.__name__ if hasattr(f, "__name__") else repr(f)
                for f in self._filters
            ]
            logger.debug(
                f"[MonsterFilter] No monsters passed current filters. "
                f"Total monsters: {len(monsters)}. Filters applied: {active_filters}"
            )

        return filtered
