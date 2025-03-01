# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from tuxemon.db import SeenStatus

logger = logging.getLogger(__name__)


@dataclass
class MonsterEntry:
    """
    Represents a monster entry in the Tuxepedia.

    Attributes:
        status: The status of the monster (seen or caught).
        appearance_count: The number of times the monster has appeared.
    """

    status: SeenStatus = SeenStatus.seen
    appearance_count: int = 1

    def update_status(self, status: SeenStatus) -> None:
        """
        Updates the status of the monster entry.

        If the current status is SeenStatus.caught and the new status is
        SeenStatus.seen, the update is ignored.

        Parameters:
            status: The new status of the monster.
        """
        if self.status != SeenStatus.caught or status != SeenStatus.seen:
            self.status = status

    def increment_appearance(self, count: int = 1) -> None:
        """
        Increments the appearance count of the monster entry.

        Parameters:
            count: The new status of the monster.
        """
        self.appearance_count += count

    def reset_entry(self) -> None:
        """
        Resets the monster entry to its initial state, with the status set
        to SeenStatus.seen and the appearance count set to 1.
        """
        self.status = SeenStatus.seen
        self.appearance_count = 1

    def get_state(self) -> dict[str, Any]:
        """
        Returns a dictionary representing the state of the monster entry,
        including its status and appearance count.

        Returns:
            A dictionary representing the state of the monster entry.
        """
        return {
            "status": self.status,
            "appearance_count": self.appearance_count,
        }


class Tuxepedia:
    """
    Represents a Tuxepedia, which is a collection of monster entries.
    """

    def __init__(self) -> None:
        """
        Initializes a new Tuxepedia object, which is an empty collection of
        monster entries.
        """
        self.entries: dict[str, MonsterEntry] = {}

    def add_entry(
        self, monster_slug: str, status: SeenStatus = SeenStatus.seen
    ) -> None:
        """
        Adds a new monster entry to the Tuxepedia. If the monster is already
        in the Tuxepedia, its status is updated.

        Parameters:
            monster_slug: The slug of the monster to add.
            status: The status of the monster (seen or caught). Defaults
            to SeenStatus.seen.
        """
        if monster_slug in self.entries:
            entry = self.entries[monster_slug]
            entry.update_status(status)
            entry.increment_appearance()
        else:
            self.entries[monster_slug] = MonsterEntry(status)

    def remove_entry(self, monster_slug: str) -> None:
        """
        Removes a monster entry from the Tuxepedia. If the monster is not
        in the Tuxepedia, a ValueError is raised.

        Parameters:
            monster_slug: The slug of the monster to remove.
        """
        if monster_slug in self.entries:
            del self.entries[monster_slug]
        else:
            raise ValueError("Monster not found in Tuxepedia")

    def get_total_monsters(self) -> int:
        """
        Returns the total number of monsters in the Tuxepedia.

        Returns:
            The total number of monsters in the Tuxepedia.
        """
        return len(self.entries)

    def get_seen_count(self) -> int:
        """
        Returns the number of monsters in the Tuxepedia that have been seen
        (i.e., their status is SeenStatus.seen).

        Returns:
            The number of monsters in the Tuxepedia that have been seen.
        """
        return sum(
            1
            for entry in self.entries.values()
            if entry.status == SeenStatus.seen
        )

    def get_caught_count(self) -> int:
        """
        Returns the number of monsters in the Tuxepedia that have been caught
        (i.e., their status is SeenStatus.caught).

        Returns:
            The number of monsters in the Tuxepedia that have been caught.
        """
        return sum(
            1
            for entry in self.entries.values()
            if entry.status == SeenStatus.caught
        )

    def get_appearance(self, monster_slug: str) -> int:
        """
        Returns the appearance count of a monster entry in the Tuxepedia.
        If the monster is not in the Tuxepedia, 0 is returned.

        Parameters:
            monster_slug: The slug of the monster to get the appearance count for.

        Returns:
            The appearance count of the monster entry.
        """
        if not self.entries:
            return 0
        return self.entries[monster_slug].appearance_count

    def get_most_frequent_monster(self) -> Optional[str]:
        """
        Returns the slug of the most frequently appearing monster in the Tuxepedia,
        or None if the Tuxepedia is empty.

        Returns:
            The slug of the most frequently appearing monster, or None if the
            Tuxepedia is empty.
        """
        if not self.entries:
            return None
        return max(
            self.entries, key=lambda slug: self.entries[slug].appearance_count
        )

    def get_most_frequent_monsters(self, n: int = 5) -> list[tuple[str, int]]:
        """
        Returns a list of the n most frequently appearing monsters in the Tuxepedia,
        along with their appearance counts. If the Tuxepedia is empty, an empty list
        is returned.

        Parameters:
            n: The number of most frequent monsters to return. Defaults to 5.

        Returns:
            A list of the n most frequently appearing monsters, along with their
            appearance counts.
        """
        if not self.entries:
            return []
        return [
            (slug, self.entries[slug].appearance_count)
            for slug in sorted(
                self.entries,
                key=lambda slug: self.entries[slug].appearance_count,
                reverse=True,
            )[:n]
        ]

    def get_monster_status_distribution(self) -> dict[SeenStatus, int]:
        """
        Returns a dictionary representing the distribution of monster statuses in
        the Tuxepedia.

        Returns:
            A dictionary representing the distribution of monster statuses.
        """
        distribution = {status: 0 for status in SeenStatus}
        for entry in self.entries.values():
            distribution[entry.status] += 1
        return distribution

    def get_completeness(self, total_monsters: int) -> float:
        """
        Returns the completeness of the Tuxepedia, which is the ratio of the number
        of monsters in the Tuxepedia to the total number of monsters.

        Parameters:
            total_monsters: The total number of monsters.

        Returns:
            The completeness of the Tuxepedia.
        """
        if total_monsters == 0:
            return 0.0
        return len(self.entries) / total_monsters

    def is_caught(self, monster_slug: str) -> bool:
        """
        Returns True if the monster with the given slug has been caught, False
        otherwise.

        Parameters:
            monster_slug: The slug of the monster to check.

        Returns:
            True if the monster has been caught, False otherwise.
        """
        if monster_slug in self.entries:
            return self.entries[monster_slug].status == SeenStatus.caught
        return False

    def is_seen(self, monster_slug: str) -> bool:
        """
        Returns True if the monster with the given slug has been seen, False
        otherwise.

        Parameters:
            monster_slug: The slug of the monster to check.

        Returns:
            True if the monster has been seen, False otherwise.
        """
        if monster_slug in self.entries:
            return self.entries[monster_slug].status == SeenStatus.seen
        return False

    def is_registered(self, monster_slug: str) -> bool:
        """
        Returns True if the monster with the given slug is in the Tuxepedia, False
        otherwise.

        Parameters:
            monster_slug: The slug of the monster to check.

        Returns:
            True if the monster is in the Tuxepedia, False otherwise.
        """
        return monster_slug in self.entries

    def get_monsters(self) -> list[str]:
        """
        Returns a list of the slugs of all monsters in the Tuxepedia.

        Returns:
            A list of the slugs of all monsters in the Tuxepedia.
        """
        return list(self.entries.keys())

    def reset(self) -> None:
        """
        Reset Tuxepedia by removing all the monsters SeenStatus.seen.
        """
        self.entries = {
            entry: monster
            for entry, monster in self.entries.items()
            if monster.status != SeenStatus.seen
        }


def decode_tuxepedia(json_data: Optional[Mapping[str, Any]]) -> Tuxepedia:
    """
    Creates a new Tuxepedia object from the given JSON data.

    Parameters:
        json_data: The JSON data to create the Tuxepedia from.

    Returns:
        A new Tuxepedia object created from the given JSON data.
    """
    tuxepedia = Tuxepedia()
    if json_data:
        for slug, entry_data in json_data.items():
            entry = MonsterEntry(**entry_data)
            tuxepedia.entries[slug] = entry
    return tuxepedia


def encode_tuxepedia(tuxepedia: Tuxepedia) -> Mapping[str, Any]:
    """
    Returns a dictionary representing the state of the given Tuxepedia.

    Parameters:
        tuxepedia: The Tuxepedia to encode.

    Returns:
        A dictionary representing the state of the given Tuxepedia.
    """
    return {
        slug: entry.get_state() for slug, entry in tuxepedia.entries.items()
    }
