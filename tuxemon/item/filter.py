# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from tuxemon.db import State
from tuxemon.item.item import Item

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


def or_filter(*filters: Callable[[Item], bool]) -> Callable[[Item], bool]:
    return lambda item: any(f(item) for f in filters)


def and_filter(*filters: Callable[[Item], bool]) -> Callable[[Item], bool]:
    return lambda item: all(f(item) for f in filters)


def not_filter(filter_func: Callable[[Item], bool]) -> Callable[[Item], bool]:
    return lambda item: not filter_func(item)


class ItemFilter:
    def __init__(self, items: list[Item]):
        self.items = items
        self._filters: list[Callable[[Item], bool]] = []

    def clear_filters(self) -> None:
        """Remove all applied filters."""
        self._filters.clear()

    def add_filter(self, filter_func: Callable[[Item], bool]) -> None:
        """Add a single filter to the filter stack."""
        self._filters.append(filter_func)

    def get_filtered_inventory(
        self, items: list[Item] | None = None
    ) -> list[Item]:
        all_items = items if items is not None else self.items
        if not self._filters:
            return all_items

        filtered = [
            item for item in all_items if all(f(item) for f in self._filters)
        ]

        if not filtered:
            active_filters = [
                f.__name__ if hasattr(f, "__name__") else str(f)
                for f in self._filters
            ]
            logger.debug(
                f"[ItemFilter] Total items: {len(all_items)}. Filters applied: {active_filters}"
            )

        return filtered

    def set_filter_all_visible(self) -> None:
        """Show only items that are visible."""
        self.clear_filters()
        self.add_filter(lambda item: item.behaviors.visible)

    def set_filter_by_category(self, category: str) -> None:
        """Show items matching a specific category and are visible."""
        self.clear_filters()
        self.add_filter(lambda item: item.category == category)
        self.add_filter(lambda item: item.behaviors.visible)

    def set_filter_usable_in_state(self, state_name: str) -> None:
        """Show items usable in the given menu state and are visible."""
        self.clear_filters()
        self.add_filter(lambda item: State[state_name] in item.usable_in)
        self.add_filter(lambda item: item.behaviors.visible)

    def set_filter_custom_or(
        self, *filter_funcs: Callable[[Item], bool]
    ) -> None:
        """Set filters with logical OR (any condition passes)."""
        self.clear_filters()
        self.add_filter(or_filter(*filter_funcs))

    def set_filter_custom_and(
        self, *filter_funcs: Callable[[Item], bool]
    ) -> None:
        """Set filters with logical AND (all conditions must pass)."""
        self.clear_filters()
        self.add_filter(and_filter(*filter_funcs))

    def set_filter_custom_not(
        self, filter_func: Callable[[Item], bool]
    ) -> None:
        """Set filter that excludes items matching the condition."""
        self.clear_filters()
        self.add_filter(not_filter(filter_func))

    def set_filter_combat_targets(
        self,
        session: Session,
        monsters: list[Monster],
        opponents: list[Monster],
    ) -> None:
        """
        Show items usable in MainCombatMenuState that are visible,
        and that have at least one valid target (monster or opponent).
        """

        def usable(item: Item) -> bool:
            return any(
                item.validate_monster(session, m) for m in monsters
            ) or (
                item.behaviors.throwable
                and any(item.validate_monster(session, o) for o in opponents)
            )

        self.clear_filters()
        self.add_filter(
            lambda item: State["MainCombatMenuState"] in item.usable_in
        )
        self.add_filter(lambda item: item.behaviors.visible)
        self.add_filter(usable)
