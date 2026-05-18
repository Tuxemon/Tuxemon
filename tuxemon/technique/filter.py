# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable

from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


def or_filter(
    *filters: Callable[[Technique], bool],
) -> Callable[[Technique], bool]:
    return lambda tech: any(f(tech) for f in filters)


def and_filter(
    *filters: Callable[[Technique], bool],
) -> Callable[[Technique], bool]:
    return lambda tech: all(f(tech) for f in filters)


def not_filter(
    filter_func: Callable[[Technique], bool],
) -> Callable[[Technique], bool]:
    return lambda tech: not filter_func(tech)


class TechFilter:
    def __init__(self, techniques: list[Technique]):
        self.techniques = techniques
        self._filters: list[Callable[[Technique], bool]] = []

    def clear_filters(self) -> None:
        """Remove all applied filters."""
        self._filters.clear()

    def add_filter(self, filter_func: Callable[[Technique], bool]) -> None:
        """Add a single filter to the filter stack."""
        self._filters.append(filter_func)

    def get_filtered_techniques(self) -> list[Technique]:
        all_techniques = self.techniques
        if not self._filters:
            return all_techniques

        filtered = [
            tech
            for tech in all_techniques
            if all(f(tech) for f in self._filters)
        ]

        if not filtered:
            active_filters = [
                f.__name__ if hasattr(f, "__name__") else repr(f)
                for f in self._filters
            ]
            logger.debug(
                f"[TechFilter] No techniques passed current filters. "
                f"Total techniques: {len(all_techniques)}. "
                f"Filters applied: {active_filters}"
            )

        return filtered

    def filter_by_type(self, type_name: str) -> None:
        self.clear_filters()
        self.add_filter(
            lambda tech: any(t.slug == type_name for t in tech.types.current)
        )

    def set_filter_custom_or(
        self, *filter_funcs: Callable[[Technique], bool]
    ) -> None:
        """Set filters with logical OR (any condition passes)."""
        self.clear_filters()
        self.add_filter(or_filter(*filter_funcs))

    def set_filter_custom_and(
        self, *filter_funcs: Callable[[Technique], bool]
    ) -> None:
        """Set filters with logical AND (all conditions must pass)."""
        self.clear_filters()
        self.add_filter(and_filter(*filter_funcs))

    def set_filter_custom_not(
        self, filter_func: Callable[[Technique], bool]
    ) -> None:
        """Set filter that excludes techniques matching the condition."""
        self.clear_filters()
        self.add_filter(not_filter(filter_func))
