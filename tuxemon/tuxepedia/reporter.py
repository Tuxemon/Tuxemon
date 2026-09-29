# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tuxemon.db import SeenStatus

if TYPE_CHECKING:
    from tuxemon.tuxepedia.data import TuxepediaData


class TuxepediaReporter:
    """
    Provides analytical functions and generates complex reports based on
    TuxepediaData.
    """

    def __init__(self, data: TuxepediaData) -> None:
        self._data = data

    def get_most_frequent_monsters(self, n: int = 5) -> list[tuple[str, int]]:
        """
        Returns a list of the n most frequently appearing monsters,
        along with their appearance counts.
        """
        if not self._data.entries:
            return []

        return [
            (slug, entry.appearance_count)
            for slug, entry in sorted(
                self._data.entries.items(),
                key=lambda item: item[1].appearance_count,
                reverse=True,
            )[:n]
        ]

    def get_completeness_report(self, total_monsters: int) -> dict[str, Any]:
        """Returns a detailed report on the Tuxepedia's completion status."""
        if total_monsters <= 0:
            return {
                "total_game": 0,
                "registered_count": 0,
                "caught_count": 0,
                "registered_percent": 0.0,
                "caught_percent": 0.0,
            }

        registered = self._data.get_total_monsters()
        caught = self._data.get_caught_count()

        return {
            "total_game": total_monsters,
            "registered_count": registered,
            "caught_count": caught,
            "registered_percent": registered / total_monsters,
            "caught_percent": caught / total_monsters,
        }

    def get_unregistered_monsters(
        self, all_monster_slugs: set[str]
    ) -> list[str]:
        """
        Returns a list of monster slugs from the complete set that are not
        yet registered in the Tuxepedia.
        """
        current_slugs = set(self._data.entries.keys())
        return list(all_monster_slugs - current_slugs)

    def get_monster_status_distribution(self) -> dict[SeenStatus, int]:
        """
        Returns a dictionary representing the distribution of monster statuses.
        """
        distribution = {
            status: 0 for status in [SeenStatus.SEEN, SeenStatus.CAUGHT]
        }
        for entry in self._data.entries.values():
            distribution[entry.status] += 1
        return distribution
