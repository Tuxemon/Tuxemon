# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from tuxemon import prepare
from tuxemon.boxes import MonsterBoxes
from tuxemon.monster import Monster, decode_monsters, encode_monsters

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class PartyHandler:
    """
    Manages a NPC's party, including adding, removing, finding,
    and switching monsters.
    """

    def __init__(
        self,
        monster_boxes: MonsterBoxes,
        owner: NPC,
        monsters: Optional[list[Monster]] = None,
        party_limit: int = prepare.PARTY_LIMIT,
    ) -> None:
        self._monsters = monsters if monsters is not None else []
        self._party_limit = party_limit
        self._monster_boxes = monster_boxes
        self._owner = owner

    @property
    def monsters(self) -> list[Monster]:
        """Returns the list of monsters in the party."""
        return self._monsters

    @property
    def party_size(self) -> int:
        """Returns the current number of monsters in the party."""
        return len(self._monsters)

    @property
    def party_limit(self) -> int:
        """Returns the maximum number of monsters allowed in the party."""
        return self._party_limit

    @property
    def level_lowest(self) -> Optional[int]:
        """Returns the lowest level among monsters in the party, or None if empty."""
        if not self._monsters:
            return None
        return min(mon.level for mon in self._monsters)

    @property
    def level_highest(self) -> Optional[int]:
        """Returns the highest level among monsters in the party, or None if empty."""
        if not self._monsters:
            return None
        return max(mon.level for mon in self._monsters)

    @property
    def level_average(self) -> Optional[int]:
        """Returns the average level of monsters in the party, or None if empty."""
        if not self._monsters:
            return None
        total = sum(mon.level for mon in self._monsters)
        return round(total / len(self._monsters))

    def add_monster(
        self,
        monster: Monster,
        slot: Optional[int] = None,
        kennel: str = prepare.KENNEL,
    ) -> None:
        """
        Adds a monster to the party. If the party is full, it sends the monster
        to the monster boxes (PCState archive).

        Parameters:
            monster: The monster to add.
            slot: Optional. The index to insert the monster at. If None or
                  party is full, it's added to the end or sent to boxes.
        """
        monster.set_owner(self._owner)

        if self.party_size >= self._party_limit:
            self._monster_boxes.add_monster(kennel, monster)
            if self._monster_boxes.is_box_full(kennel):
                self._monster_boxes.create_and_merge_box(kennel)
        else:
            if slot is not None and 0 <= slot <= self.party_size:
                self._monsters.insert(slot, monster)
            else:
                self._monsters.append(monster)

    def find_monster(self, monster_slug: str) -> Optional[Monster]:
        """
        Finds a monster in the party by its slug.

        Parameters:
            monster_slug: The slug name of the monster.

        Returns:
            Monster found, or None.
        """
        for monster in self._monsters:
            if monster.slug == monster_slug:
                return monster
        return None

    def find_monster_by_id(self, instance_id: UUID) -> Optional[Monster]:
        """
        Finds a monster in the party by its instance ID.

        Parameters:
            instance_id: The instance_id of the monster.

        Returns:
            Monster found, or None.
        """
        return next(
            (m for m in self._monsters if m.instance_id == instance_id), None
        )

    def find_monster_by_tech_id(self, instance_id: UUID) -> Optional[Monster]:
        """
        Finds a monster in the party by its technique instance ID.

        Parameters:
            instance_id: The instance_id of the technique.

        Returns:
            Monster found, or None.
        """
        return next(
            (
                monster
                for monster in self._monsters
                if monster.moves.find_tech_by_id(instance_id)
            ),
            None,
        )

    def release_monster(self, monster: Monster) -> bool:
        """
        Releases a monster from this party. Used to release into the wild.
        Prevents releasing the last monster if the party is not empty.

        Parameters:
            monster: Monster to release into the wild.

        Returns:
            True if the monster was successfully released, False otherwise.
        """
        if self.party_size <= 1:
            return False

        if monster in self._monsters:
            self.remove_monster(monster)
            monster.owner = None
            return True
        else:
            return False

    def remove_monster(self, monster: Monster) -> None:
        """
        Removes a monster from this party.

        Parameters:
            monster: Monster to remove from the party.
        """
        if monster in self._monsters:
            self._monsters.remove(monster)

    def switch_monsters(self, index_1: int, index_2: int) -> None:
        """
        Swaps two monsters in this party by their indices.

        Parameters:
            index_1: The index of the first monster.
            index_2: The index of the second monster.
        """
        if not (
            0 <= index_1 < self.party_size and 0 <= index_2 < self.party_size
        ):
            raise IndexError("Indices out of bounds for party size.")

        self._monsters[index_1], self._monsters[index_2] = (
            self._monsters[index_2],
            self._monsters[index_1],
        )

    def has_monster(self, monster: Monster) -> bool:
        """
        Checks if a given monster is in the party.

        Parameters:
            monster: The monster to check.

        Returns:
            True if the monster is in the party, False otherwise.
        """
        return monster in self._monsters

    def has_tech(self, tech_slug: str) -> bool:
        """
        Returns True if any monster in the party has the given technique.

        Parameters:
            tech_slug: The slug name of the technique.
        """
        for monster in self._monsters:
            if monster.moves.has_move(tech_slug):
                return True
        return False

    def replace_monster(
        self, old_monster: Monster, new_monster: Monster
    ) -> bool:
        """
        Replaces an existing monster in the party with a new one.

        Parameters:
            old_monster: The monster to replace.
            new_monster: The new monster.

        Returns:
            True if successful, False otherwise.
        """
        if old_monster in self._monsters:
            index = self._monsters.index(old_monster)
            self._monsters[index] = new_monster
            new_monster.owner = self._owner
            return True
        return False

    def has_type(self, element_slug: str) -> bool:
        """
        Returns True if any monster in the party has the given type.
        """
        return any(mon.has_type(element_slug) for mon in self._monsters)

    def clear_party(self) -> None:
        """
        Removes all monsters from the party and clears their ownership.
        """
        if self._monsters:
            for monster in self._monsters:
                monster.owner = None
        self._monsters.clear()

    def get_alignment(self) -> Optional[str]:
        """
        Returns the dominant elemental type in the party,
        based on the most frequently occurring type among monsters.
        If no types are found, returns None.
        """
        type_counter: Counter[str] = Counter()

        for monster in self._monsters:
            try:
                type_slugs = monster.types.get_type_slugs()
                type_counter.update(type_slugs)
            except Exception:
                continue  # Skip if the monster has no types

        if not type_counter:
            return None

        dominant_type, _ = type_counter.most_common(1)[0]
        return dominant_type

    def replace_party(
        self, new_monsters: list[Monster], add_overflow_to_box: bool = True
    ) -> None:
        """
        Replaces the entire party with a new list of monsters.

        Parameters:
            new_monsters: The new monsters to set as the party.
            add_overflow_to_box:
                If True, overflow monsters are added to the box.
                If False, overflow monsters are discarded.
        """
        self.clear_party()

        for monster in new_monsters[: self._party_limit]:
            monster.set_owner(self._owner)
            self._monsters.append(monster)

        if add_overflow_to_box:
            overflow = new_monsters[self._party_limit :]
            for monster in overflow:
                monster.set_owner(self._owner)
                self._monster_boxes.add_monster(prepare.KENNEL, monster)
                if self._monster_boxes.is_box_full(prepare.KENNEL):
                    self._monster_boxes.create_and_merge_box(prepare.KENNEL)

    def encode_party(self) -> Sequence[Mapping[str, Any]]:
        return encode_monsters(self._monsters)

    def decode_party(self, json_data: Optional[Mapping[str, Any]]) -> None:
        self.clear_party()
        if json_data and "monsters" in json_data:
            for mon in decode_monsters(json_data["monsters"]):
                self.add_monster(mon, self.party_size)
