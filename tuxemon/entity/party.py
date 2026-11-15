# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tuxemon.boxes import MonsterBoxes
from tuxemon.entity.party_stats import PartyStats
from tuxemon.entity.routing import RoutingPolicy, RoutingPolicyRegistry
from tuxemon.monster.monster import Monster, decode_monsters, encode_monsters
from tuxemon.platform.const.sizes import PARTY_LIMIT

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.save_system.save_state import NPCState

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
        monsters: list[Monster] | None = None,
        party_limit: int = PARTY_LIMIT,
        routing_policy_name: str = "default",
    ) -> None:
        self._monsters = monsters if monsters is not None else []
        self._party_limit = party_limit
        self._monster_boxes = monster_boxes
        self._owner = owner
        self._routing_policy_name = routing_policy_name

    @property
    def owner(self) -> NPC:
        return self._owner

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
        return self._monsters

    @property
    def party_size(self) -> int:
        return len(self._monsters)

    @property
    def party_limit(self) -> int:
        return self._party_limit

    @property
    def level_lowest(self) -> int | None:
        return PartyStats.calculate_level_lowest(self._monsters)

    @property
    def level_highest(self) -> int | None:
        return PartyStats.calculate_level_highest(self._monsters)

    @property
    def level_average(self) -> int | None:
        return PartyStats.calculate_level_average(self._monsters)

    @property
    def alignment(self) -> str | None:
        return PartyStats.get_alignment(self._monsters)

    @property
    def no_tech(self) -> list[str]:
        return PartyStats.no_tech(self._monsters)

    @property
    def is_fainted(self) -> bool:
        return PartyStats.is_fainted(self._monsters)

    @property
    def alive(self) -> list[Monster]:
        return PartyStats.alive(self._monsters)

    @property
    def missing_hp_total(self) -> int:
        return PartyStats.missing_hp_total(self._monsters)

    @property
    def is_healed(self) -> bool:
        return PartyStats.is_healed(self._monsters)

    def has_tech(self, tech_slug: str) -> bool:
        return PartyStats.has_tech(self._monsters, tech_slug)

    def _resolve_policy(self, override: str | None) -> RoutingPolicy:
        return (
            RoutingPolicyRegistry.get(override)
            if override
            else self.routing_policy
        )

    def _assign_owner(self, monster: Monster) -> None:
        monster.set_owner(self._owner)

    def _validate_index(self, index: int) -> None:
        if not (0 <= index < self.party_size):
            raise IndexError("Index out of bounds for party size.")

    def _find(self, predicate: Callable[[Monster], bool]) -> Monster | None:
        return next((m for m in self._monsters if predicate(m)), None)

    def _compute_party_and_overflow(
        self, monsters: list[Monster], policy: RoutingPolicy
    ) -> tuple[list[Monster], list[Monster]]:
        if policy.max_party_size == -1:
            return monsters, []
        limit = policy.max_party_size or self._party_limit
        return monsters[:limit], monsters[limit:]

    def _route_monster(
        self,
        monster: Monster,
        slot: int | None,
        policy: RoutingPolicy,
        kennel: str | None,
    ) -> None:
        if self.should_send_to_box(policy):
            self.send_monster_to_box(monster, kennel)
        else:
            self.insert_monster_to_party(monster, slot)

    def apply_nickname_rules(
        self, monster: Monster, policy: RoutingPolicy | None = None
    ) -> None:
        policy = policy or self.routing_policy
        rules = policy.nickname_rules

        if not rules:
            return

        base_name = monster.name
        monster.name = (
            f"{rules.get('prefix', '')}{base_name}{rules.get('suffix', '')}"
        )

    def should_send_to_box(self, policy: RoutingPolicy | None = None) -> bool:
        policy = policy or self.routing_policy
        if policy.should_force_to_box() or not policy.allow_party_addition:
            return True
        if policy.max_party_size == -1:
            return False
        limit = policy.max_party_size or self._party_limit
        return self.party_size >= limit

    def send_monster_to_box(
        self, monster: Monster, kennel: str | None = None
    ) -> bool:
        policy = self.routing_policy
        return self._monster_boxes.attempt_add_monster(monster, policy, kennel)

    def insert_monster_to_party(
        self, monster: Monster, slot: int | None = None
    ) -> None:
        self._assign_owner(monster)
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
        slot: int | None = None,
        kennel: str | None = None,
        override_policy_name: str | None = None,
    ) -> None:
        policy = self._resolve_policy(override_policy_name)
        logger.debug(
            f"Adding monster '{monster}' using policy '{policy.name}'"
        )
        self.apply_nickname_rules(monster, policy)
        self._assign_owner(monster)
        self._route_monster(monster, slot, policy, kennel)

    def find_monster(self, monster_slug: str) -> Monster | None:
        return self._find(lambda m: m.slug == monster_slug)

    def find_monster_by_id(self, instance_id: UUID) -> Monster | None:
        return self._find(lambda m: m.instance_id == instance_id)

    def find_monster_by_tech_id(self, instance_id: UUID) -> Monster | None:
        return self._find(
            lambda m: m.moves.find_tech_by_id(instance_id) is not None
        )

    def release_monster(self, monster: Monster) -> bool:
        if self.party_size <= 1:
            return False
        if monster not in self._monsters:
            return False

        self.remove_monster(monster)
        return True

    def remove_monster(self, monster: Monster) -> None:
        if monster in self._monsters:
            self._monsters.remove(monster)
            monster.owner = None

    def switch_monsters(self, index_1: int, index_2: int) -> None:
        self._validate_index(index_1)
        self._validate_index(index_2)
        self._monsters[index_1], self._monsters[index_2] = (
            self._monsters[index_2],
            self._monsters[index_1],
        )

    def has_monster(self, monster: Monster) -> bool:
        return monster in self._monsters

    def replace_monster(
        self, old_monster: Monster, new_monster: Monster
    ) -> bool:
        if old_monster not in self._monsters:
            return False
        index = self._monsters.index(old_monster)
        old_monster.owner = None
        self._monsters[index] = new_monster
        self._assign_owner(new_monster)
        return True

    def clear_party(self) -> None:
        for monster in self._monsters:
            monster.owner = None
        self._monsters.clear()

    def replace_party(
        self,
        new_monsters: list[Monster],
        add_overflow_to_box: bool = True,
        override_policy_name: str | None = None,
    ) -> None:
        self.clear_party()

        policy = self._resolve_policy(override_policy_name)
        party_monsters, overflow = self._compute_party_and_overflow(
            new_monsters, policy
        )

        for monster in party_monsters:
            self._assign_owner(monster)

        self._monsters.extend(party_monsters)

        if add_overflow_to_box and overflow:
            kennel = policy.get_kennel()
            for monster in overflow:
                self._assign_owner(monster)
                self.send_monster_to_box(monster, kennel)

    def transfer_monster_to_box(
        self, monster: Monster, kennel: str | None = None
    ) -> bool:
        if not self.has_monster(monster):
            logger.error(f"Monster '{monster}' not found in party.")
            return False

        success = self.send_monster_to_box(monster, kennel)
        if not success:
            logger.warning(
                f"Failed to transfer monster '{monster}' to box; "
                "leaving party unchanged."
            )
            return False

        self.remove_monster(monster)
        return True

    def transfer_monster_to_party(
        self,
        monster: Monster,
        slot: int | None = None,
        source_kennel: str | None = None,
    ) -> bool:
        if self.should_send_to_box():
            logger.warning(
                f"Cannot transfer monster '{monster}' to party: policy or limit prevents it."
            )
            return False  # monster stays in box, nothing mutated yet

        self._monster_boxes.remove_from_box("monster", source_kennel, monster)
        self.insert_monster_to_party(monster, slot)
        logger.info(f"Monster '{monster}' transferred from box to party.")
        return True

    def encode_party(self) -> Sequence[Mapping[str, Any]]:
        return encode_monsters(self._monsters)

    def decode_party(self, json_data: NPCState | None) -> None:
        # Bypasses add_monster intentionally: save/load restores state directly
        # without applying routing policy, nickname rules, or capacity checks.
        self.clear_party()
        if not json_data or not json_data.monsters:
            return

        for mon in decode_monsters(json_data.monsters):
            mon.set_owner(self._owner)
            self._monsters.append(mon)
