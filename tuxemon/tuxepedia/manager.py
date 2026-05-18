# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from tuxemon.db import SeenStatus
from tuxemon.tuxepedia.data import TuxepediaData

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

    status: SeenStatus = SeenStatus.SEEN
    appearance_count: int = 1
    caught_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.status, SeenStatus):
            try:
                self.status = SeenStatus(self.status)
            except ValueError:
                self.status = SeenStatus.SEEN
        self._validate()

    def update_status(self, status: SeenStatus) -> None:
        """Prevents status downgrade from caught to seen."""
        if self.status == SeenStatus.CAUGHT and status == SeenStatus.SEEN:
            return

        self.appearance_count += 1

        if status == SeenStatus.CAUGHT and self.status != SeenStatus.CAUGHT:
            self.caught_count += 1

        self.status = status
        self._validate()

    def reset_entry(self) -> None:
        """
        Resets the monster entry to its initial state, with the status set
        to SeenStatus.SEEN and the appearance count set to 1.
        """
        self.status = SeenStatus.SEEN
        self.appearance_count = 1
        self.caught_count = 0
        self._validate()

    def get_state(self) -> dict[str, Any]:
        """Returns state for serialization."""
        return {
            "status": self.status.value,
            "appearance_count": self.appearance_count,
            "caught_count": self.caught_count,
        }

    def _validate(self) -> None:
        assert self.appearance_count >= 1
        assert self.caught_count >= 0
        assert self.caught_count <= self.appearance_count

    def register_appearance(self) -> None:
        self.appearance_count += 1
        self._validate()

    def __str__(self) -> str:
        return (
            f"MonsterEntry(status={self.status.name}, "
            f"appearance_count={self.appearance_count}, "
            f"caught_count={self.caught_count})"
        )


class TuxepediaManager:
    """
    Manages the Tuxepedia data, handling all state changes and event publishing.
    This class is the main interface for game systems to update the encyclopedia.
    """

    def __init__(
        self,
        event_bus: EventBus,
        initial_entries: dict[str, MonsterEntry] | None = None,
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

    def register_seen(self, slug: str) -> None:
        """Record that a monster was seen."""
        self._apply_status(slug, SeenStatus.SEEN)

    def register_caught(self, slug: str) -> None:
        """Record that a monster was caught."""
        self._apply_status(slug, SeenStatus.CAUGHT)

    def register_appearance(self, slug: str) -> None:
        """Record an appearance without changing status."""
        entry = self._data.get_entry_for_mutation(slug)
        if entry:
            entry.register_appearance()
            self._event_bus.publish(
                EVENT_MONSTER_STATUS_UPDATED,
                monster_slug=slug,
                status=entry.status,
                appearance_count=entry.appearance_count,
                caught_count=entry.caught_count,
                status_changed=False,
            )
        else:
            # First appearance = seen
            self.register_seen(slug)

    def _apply_status(self, slug: str, status: SeenStatus) -> None:
        entry = self._data.get_entry_for_mutation(slug)

        if entry:
            old_status = entry.status
            entry.update_status(status)

            self._event_bus.publish(
                EVENT_MONSTER_STATUS_UPDATED,
                monster_slug=slug,
                status=entry.status,
                appearance_count=entry.appearance_count,
                caught_count=entry.caught_count,
                status_changed=(entry.status != old_status),
            )
        else:
            new_entry = MonsterEntry(status)
            self._data.set_entry(slug, new_entry)

            self._event_bus.publish(
                EVENT_MONSTER_ADDED,
                monster_slug=slug,
                status=new_entry.status,
                appearance_count=new_entry.appearance_count,
                caught_count=new_entry.caught_count,
            )

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
                if entry.status == SeenStatus.SEEN
            }
            new_entries = {
                slug: entry
                for slug, entry in current_entries.items()
                if entry.status != SeenStatus.SEEN
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


def decode_tuxepedia(
    json_data: Mapping[str, Any] | None, event_bus: EventBus
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
