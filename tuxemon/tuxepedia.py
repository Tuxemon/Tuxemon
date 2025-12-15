# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.db import SeenStatus

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus

logger = logging.getLogger(__name__)

EVENT_MONSTER_ADDED = "TUXEPEDIA_MONSTER_ADDED"
EVENT_MONSTER_STATUS_UPDATED = "TUXEPEDIA_MONSTER_STATUS_UPDATED"
EVENT_MONSTER_REMOVED = "TUXEPEDIA_MONSTER_REMOVED"
EVENT_TUXEPEDIA_RESET = "TUXEPEDIA_RESET"


@dataclass
class MonsterEntry:
    """
    Represents a monster entry in the Tuxepedia, tracking status and appearance
    count.
    """

    status: SeenStatus = SeenStatus.seen
    appearance_count: int = 1
    caught_count: int = 0

    def update_status(self, status: SeenStatus) -> None:
        """Prevents status downgrade from caught to seen."""
        if self.status == SeenStatus.caught and status == SeenStatus.seen:
            return

        self.appearance_count += 1

        if status == SeenStatus.caught and self.status != SeenStatus.caught:
            self.caught_count += 1

        self.status = status

    def reset_entry(self) -> None:
        """
        Resets the monster entry to its initial state, with the status set
        to SeenStatus.seen and the appearance count set to 1.
        """
        self.status = SeenStatus.seen
        self.appearance_count = 1
        self.caught_count = 0

    def get_state(self) -> dict[str, Any]:
        """Returns state for serialization."""
        return {
            "status": self.status,
            "appearance_count": self.appearance_count,
            "caught_count": self.caught_count,
        }

    def __str__(self) -> str:
        return (
            f"MonsterEntry(status={self.status.name}, "
            f"appearance_count={self.appearance_count}, "
            f"caught_count={self.caught_count})"
        )


class TuxepediaData:
    """
    The core, read-only data structure containing all monster entries.
    Provides safe reading and basic count queries.
    """

    def __init__(
        self, entries: Optional[dict[str, MonsterEntry]] = None
    ) -> None:
        self._entries: dict[str, MonsterEntry] = (
            entries if entries is not None else {}
        )

    def _set_entries(self, new_entries: dict[str, MonsterEntry]) -> None:
        """
        Allows the trusted Manager to replace the entry set (e.g., during reset).
        """
        self._entries = new_entries

    def get_entry_for_mutation(
        self, monster_slug: str
    ) -> Optional[MonsterEntry]:
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
            if entry.status == SeenStatus.caught
        )

    def get_seen_count(self) -> int:
        return sum(
            1
            for entry in self._entries.values()
            if entry.status == SeenStatus.seen
        )

    def get_status(self, monster_slug: str) -> Optional[SeenStatus]:
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
        return bool(entry and entry.status == SeenStatus.seen)

    def is_caught(self, monster_slug: str) -> bool:
        entry = self._entries.get(monster_slug)
        return bool(entry and entry.status == SeenStatus.caught)

    def get_monsters(self) -> list[str]:
        return list(self._entries.keys())


class TuxepediaManager:
    """
    Manages the Tuxepedia data, handling all state changes and event publishing.
    This class is the main interface for game systems to update the encyclopedia.
    """

    def __init__(
        self,
        event_bus: EventBus,
        initial_entries: Optional[dict[str, MonsterEntry]] = None,
    ) -> None:
        """Initializes the manager, optionally loading data via initial_entries."""
        self._event_bus = event_bus
        self._data = TuxepediaData(initial_entries)

    @property
    def data(self) -> TuxepediaData:
        """Provides read-only access to the core data structure."""
        return self._data

    def is_registered(self, monster_slug: str) -> bool:
        return self._data.is_registered(monster_slug)

    def is_seen(self, monster_slug: str) -> bool:
        return self._data.is_seen(monster_slug)

    def is_caught(self, monster_slug: str) -> bool:
        return self._data.is_caught(monster_slug)

    def get_caught_count(self) -> int:
        return self._data.get_caught_count()

    def get_seen_count(self) -> int:
        return self._data.get_seen_count()

    def get_monsters(self) -> list[str]:
        return self._data.get_monsters()

    def add_entry(
        self, monster_slug: str, status: SeenStatus = SeenStatus.seen
    ) -> None:
        """Adds a new monster entry or updates an existing one, publishing events."""

        entry = self._data.get_entry_for_mutation(monster_slug)

        if entry:
            old_status = entry.status
            entry.update_status(status)

            self._event_bus.publish(
                EVENT_MONSTER_STATUS_UPDATED,
                monster_slug=monster_slug,
                status=entry.status,
                appearance_count=entry.appearance_count,
                caught_count=entry.caught_count,
                status_changed=(entry.status != old_status),
            )
            logger.debug(
                f"Updated monster {monster_slug}: entry={entry}",
            )
        else:
            new_entry = MonsterEntry(status)
            self._data.set_entry(monster_slug, new_entry)

            self._event_bus.publish(
                EVENT_MONSTER_ADDED,
                monster_slug=monster_slug,
                status=status,
                appearance_count=new_entry.appearance_count,
                caught_count=new_entry.caught_count,
            )
            logger.debug(f"Added monster {monster_slug} with status={status}")

    def remove_entry(self, monster_slug: str) -> None:
        """Removes a monster entry and publishes the relevant event."""

        entry = self._data.get_entry_for_mutation(monster_slug)

        if not entry:
            raise ValueError("Monster not found in Tuxepedia")

        status = entry.status
        appearance_count = entry.appearance_count
        caught_count = entry.caught_count

        self._data.delete_entry(monster_slug)

        self._event_bus.publish(
            EVENT_MONSTER_REMOVED,
            monster_slug=monster_slug,
            status=status,
            appearance_count=appearance_count,
            caught_count=caught_count,
        )
        logger.debug(
            f"Removed monster {monster_slug} (entry={entry})",
        )

    def reset(self, remove_seen_only: bool = True) -> None:
        """Resets Tuxepedia entries and publishes the reset event."""
        initial_count = self._data.get_total_monsters()
        current_entries = self._data.entries

        if remove_seen_only:
            removed_entries = {
                slug: entry
                for slug, entry in current_entries.items()
                if entry.status == SeenStatus.seen
            }
            new_entries = {
                slug: entry
                for slug, entry in current_entries.items()
                if entry.status != SeenStatus.seen
            }
            self._data._set_entries(new_entries)
        else:
            removed_entries = current_entries
            self._data._set_entries({})

        final_count = self._data.get_total_monsters()
        self._event_bus.publish(
            EVENT_TUXEPEDIA_RESET,
            removed_count=initial_count - final_count,
            remaining_count=final_count,
            remove_seen_only=remove_seen_only,
            removed_monsters=[
                {
                    "slug": slug,
                    "status": entry.status,
                    "appearance_count": entry.appearance_count,
                    "caught_count": entry.caught_count,
                }
                for slug, entry in removed_entries.items()
            ],
        )
        logger.debug(
            f"Tuxepedia reset: removed={initial_count - final_count}, remaining={final_count}, remove_seen_only={remove_seen_only}",
        )


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
            status: 0 for status in [SeenStatus.seen, SeenStatus.caught]
        }
        for entry in self._data.entries.values():
            distribution[entry.status] += 1
        return distribution


def decode_tuxepedia(
    json_data: Optional[Mapping[str, Any]], event_bus: EventBus
) -> TuxepediaManager:
    """
    Creates a new TuxepediaManager object from the given JSON data.

    Parameters:
        json_data: The JSON data (slug -> entry_data) to create the Tuxepedia from.
        event_bus: The game's event bus.

    Returns:
        A new TuxepediaManager object with loaded data.
    """
    loaded_entries: dict[str, MonsterEntry] = {}
    if json_data:
        for slug, entry_data in json_data.items():
            loaded_entries[slug] = MonsterEntry(**entry_data)

    return TuxepediaManager(event_bus, initial_entries=loaded_entries)


def encode_tuxepedia(manager: TuxepediaManager) -> Mapping[str, Any]:
    """
    Returns a dictionary representing the state of the given Tuxepedia for saving.

    Parameters:
        manager: The TuxepediaManager to encode.

    Returns:
        A dictionary representing the state of all monster entries.
    """
    return {
        slug: entry.get_state() for slug, entry in manager.data.entries.items()
    }
