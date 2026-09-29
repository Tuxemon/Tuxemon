# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.db import SeenStatus

if TYPE_CHECKING:
    from tuxemon.tuxepedia.manager import MonsterEntry


class TuxepediaData:
    """
    The core, read-only data structure containing all monster entries.
    Provides safe reading and basic count queries.
    """

    def __init__(self, entries: dict[str, MonsterEntry] | None = None) -> None:
        self._entries: dict[str, MonsterEntry] = (
            entries if entries is not None else {}
        )

    def _set_entries(self, new_entries: dict[str, MonsterEntry]) -> None:
        """
        Allows the trusted Manager to replace the entry set (e.g., during reset).
        """
        self._entries = new_entries

    def get_entry_for_mutation(self, monster_slug: str) -> MonsterEntry | None:
        """
        Returns the actual entry object (not a copy) for in-place modification
        by the Manager.
        """
        return self._entries.get(monster_slug)

    def set_entry(self, monster_slug: str, entry: MonsterEntry) -> None:
        """Adds or replaces a single entry (used for initial add)."""
        self._entries[monster_slug] = entry

    def delete_entry(self, monster_slug: str) -> None:
        """Deletes a single entry (used for remove)."""
        if monster_slug in self._entries:
            del self._entries[monster_slug]
        else:
            raise KeyError(f"Entry {monster_slug} not found.")

    @property
    def entries(self) -> dict[str, MonsterEntry]:
        """Returns a copy of the entries for safe reading."""
        return dict(self._entries)

    def get_total_monsters(self) -> int:
        return len(self._entries)

    def get_caught_count(self) -> int:
        return sum(
            1
            for entry in self._entries.values()
            if entry.status == SeenStatus.CAUGHT
        )

    def get_seen_count(self) -> int:
        return sum(
            1
            for entry in self._entries.values()
            if entry.status == SeenStatus.SEEN
        )

    def get_status(self, monster_slug: str) -> SeenStatus | None:
        entry = self._entries.get(monster_slug)
        return entry.status if entry else None

    def get_appearance(self, monster_slug: str) -> int:
        entry = self._entries.get(monster_slug)
        return entry.appearance_count if entry else 0

    def get_caught(self, monster_slug: str) -> int:
        entry = self._entries.get(monster_slug)
        return entry.caught_count if entry else 0

    def is_registered(self, monster_slug: str) -> bool:
        return monster_slug in self._entries

    def is_seen(self, monster_slug: str) -> bool:
        entry = self._entries.get(monster_slug)
        return bool(entry and entry.status == SeenStatus.SEEN)

    def is_caught(self, monster_slug: str) -> bool:
        entry = self._entries.get(monster_slug)
        return bool(entry and entry.status == SeenStatus.CAUGHT)

    def get_monsters(self) -> list[str]:
        return list(self._entries.keys())
