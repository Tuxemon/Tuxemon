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
from tuxemon.entity_dir.routing import RoutingPolicy, RoutingPolicyRegistry
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
        routing_policy_name: str = "default",
    ) -> None:
        self._monsters = monsters if monsters is not None else []
        self._party_limit = party_limit
        self._monster_boxes = monster_boxes
        self._owner = owner
        self._routing_policy_name = routing_policy_name

    @property
    def routing_policy(self) -> RoutingPolicy:
        return RoutingPolicyRegistry.get(self._routing_policy_name)

    @property
    def routing_policy_name(self) -> str:
        return self._routing_policy_name

    @routing_policy_name.setter
    def routing_policy_name(self, name: str) -> None:
        if not RoutingPolicyRegistry.has(name):
            raise ValueError(f"Unknown routing policy: {name}")
        self._routing_policy_name = name

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

    def apply_nickname_rules(self, monster: Monster) -> None:
        policy = self.routing_policy
        base_name = monster.name
        rules = policy.nickname_rules
        nick = f"{rules.get('prefix', '')}{base_name}{rules.get('suffix', '')}"
        monster.name = nick

    def should_send_to_box(
        self, policy: Optional[RoutingPolicy] = None
    ) -> bool:
        policy = policy or self.routing_policy

        is_unlimited = (
            policy.max_party_size is not None and policy.max_party_size == -1
        )
        party_limit = (
            policy.max_party_size
            if policy.max_party_size is not None
            else self._party_limit
        )

        return (
            policy.should_force_to_box()
            or not policy.allow_party_addition
            or (not is_unlimited and self.party_size >= party_limit)
        )

    def send_monster_to_box(
        self, monster: Monster, kennel: Optional[str] = None
    ) -> None:
        policy = self.routing_policy
        kennel = kennel if kennel is not None else policy.get_kennel()
        max_box_capacity = policy.max_box_capacity or prepare.MAX_KENNEL

        if self._monster_boxes.is_box_full(kennel, max_box_capacity):
            logger.warning(
                f"Primary box '{kennel}' is full under policy '{policy.name}'."
            )

            overflow_kennel = policy.overflow_kennel
            if overflow_kennel:
                logger.info(
                    f"Attempting to use overflow kennel '{overflow_kennel}'."
                )
                if not self._monster_boxes.is_box_full(overflow_kennel):
                    self._monster_boxes.add_monster(overflow_kennel, monster)
                    logger.info(
                        f"Monster '{monster}' added to overflow kennel '{overflow_kennel}'."
                    )
                    return
                else:
                    logger.warning(
                        f"Overflow kennel '{overflow_kennel}' is also full."
                    )

            if policy.kennel_name_rules:
                logger.info(
                    f"Creating overflow box using kennel_name_rules for base '{kennel}'."
                )
                self._monster_boxes.create_and_merge_box(
                    kennel, policy.kennel_name_rules
                )
                self._monster_boxes.add_monster(kennel, monster)
                return

            # Final fallback: release if allowed
            if policy.auto_release_if_box_full:
                logger.info(
                    f"Monster '{monster}' discarded due to full boxes and no overflow options."
                )
                return

            # Otherwise, monster is lost or error
            logger.error(
                f"Monster '{monster}' could not be stored. All boxes full and no overflow strategy."
            )
            return

        # Normal case
        self._monster_boxes.add_monster(kennel, monster)
        logger.info(f"Monster '{monster}' added to box '{kennel}'.")

    def insert_monster_to_party(
        self, monster: Monster, slot: Optional[int] = None
    ) -> None:
        if slot is None:
            self._monsters.append(monster)
        elif 0 <= slot <= self.party_size:
            self._monsters.insert(slot, monster)
        else:
            raise IndexError(
                f"Invalid slot {slot} for party size {self.party_size}"
            )

    def add_monster(
        self,
        monster: Monster,
        slot: Optional[int] = None,
        kennel: Optional[str] = None,
        override_policy_name: Optional[str] = None,
    ) -> None:
        """
        Adds a monster to the party. If the party is full, it sends the monster
        to the monster boxes (PCState archive).

        Parameters:
            monster: The monster to add.
            slot: Optional. The index to insert the monster at. If None or
                party is full, it's added to the end or sent to boxes.
            override_policy_name: Optional. A temporary policy name to use for
                this call.
        """
        policy_to_use = (
            RoutingPolicyRegistry.get(override_policy_name)
            if override_policy_name
            else self.routing_policy
        )
        logger.debug(
            f"Adding monster '{monster}' using policy '{policy_to_use.name}'"
        )

        self.apply_nickname_rules(monster)
        monster.set_owner(self._owner)

        if self.should_send_to_box(policy_to_use):
            self.send_monster_to_box(monster, kennel)
        else:
            self.insert_monster_to_party(monster, slot)

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
        self,
        new_monsters: list[Monster],
        add_overflow_to_box: bool = True,
        override_policy_name: Optional[str] = None,
    ) -> None:
        """
        Replaces the entire party with a new list of monsters, handling overflow
        based on the current or an overridden routing policy.
        """
        self.clear_party()

        if override_policy_name:
            policy = RoutingPolicyRegistry.get(override_policy_name)
        else:
            policy = self.routing_policy

        party_limit = (
            policy.max_party_size
            if policy.max_party_size is not None
            else self._party_limit
        )

        if policy.max_party_size == -1:
            party_monsters = new_monsters
            overflow = []
        else:
            party_limit = policy.max_party_size or self._party_limit
            party_monsters = new_monsters[:party_limit]
            overflow = new_monsters[party_limit:]

        for monster in party_monsters:
            monster.set_owner(self._owner)
            self._monsters.append(monster)

        if add_overflow_to_box and overflow:
            kennel_for_overflow = policy.get_kennel()
            for monster in overflow:
                monster.set_owner(self._owner)
                self.send_monster_to_box(monster, kennel_for_overflow)

    def transfer_monster_to_box(
        self, monster: Monster, kennel: Optional[str] = None
    ) -> bool:
        if not self.has_monster(monster):
            logger.error(f"Monster '{monster}' not found in party.")
            return False

        self.remove_monster(monster)
        self.send_monster_to_box(monster, kennel)
        logger.info(f"Monster '{monster}' transferred from party to box.")
        return True

    def transfer_monster_to_party(
        self, monster: Monster, slot: Optional[int] = None
    ) -> bool:
        if self.should_send_to_box():
            logger.warning(
                f"Cannot transfer monster '{monster}' to party: policy or limit prevents it."
            )
            return False

        self.insert_monster_to_party(monster, slot)
        logger.info(f"Monster '{monster}' transferred from box to party.")
        return True

    def encode_party(self) -> Sequence[Mapping[str, Any]]:
        return encode_monsters(self._monsters)

    def decode_party(self, json_data: Optional[Mapping[str, Any]]) -> None:
        self.clear_party()
        if json_data and "monsters" in json_data:
            for mon in decode_monsters(json_data["monsters"]):
                self.add_monster(mon, self.party_size)
