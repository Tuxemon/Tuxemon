# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any

from tuxemon.database.runtime import db
from tuxemon.db import (
    FactionAlignment,
    FactionKind,
    FactionModel,
    FactionRelationStatus,
    RankStep,
)
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus
    from tuxemon.game_variables import GameVariablesManager

logger = logging.getLogger(__name__)


class FactionEvent(Enum):
    RELATION_CHANGED = "faction_relation_changed"
    MEMBER_JOINED = "faction_member_joined"
    MEMBER_REMOVED = "faction_member_removed"
    PROMOTED = "faction_npc_promoted"
    DEMOTED = "faction_npc_demoted"


class Faction:
    """
    Represents a faction within the Tuxemon game world.

    This class manages all aspects of a faction, including its identity,
    relationships with other factions, and the status of its members.
    It handles reputation tracking for individual NPCs, determines their ranks
    within the faction, and manages their membership.
    """

    MAX_PUBLIC_REPUTATION: int = 100

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus
        self._rank_cache: dict[str, str] = {}
        self.slug: str = ""
        self._custom_name: str | None = None
        self._custom_description: str | None = None
        self.kind: FactionKind | None = None
        self.alignment: FactionAlignment | None = None
        self.badge_id: str | None = None
        self.leader_char: str | None = None
        self.ranks: list[RankStep] = []
        self.members: list[str] = []
        self.reputation: dict[str, int] = {}
        self.relations: dict[str, FactionRelationStatus] = {}
        self._public_reputation: int = 0
        self._decay_timer: float = 0.0
        self._decay_interval: float = 600.0
        self._decay_rate: float = 0.05
        self._neutral_baseline: int = 50

    @property
    def name(self) -> str:
        return self._custom_name or T.translate(self.slug)

    @name.setter
    def name(self, value: str) -> None:
        self._custom_name = value

    @property
    def description(self) -> str:
        return self._custom_description or T.translate(
            f"{self.slug}_description"
        )

    @description.setter
    def description(self, value: str) -> None:
        self._custom_description = value

    @classmethod
    def load_from_db(cls, slug: str) -> Faction:
        """
        Factory method to load and return a Faction instance from the db.
        """
        results = FactionModel.lookup(slug, db)
        faction = cls()
        faction._populate_from_model(results)
        return faction

    def update(self, dt: float) -> None:
        self._decay_timer += dt

        if self._public_reputation != self._neutral_baseline:
            change = (
                (self._neutral_baseline - self._public_reputation)
                * dt
                * self._decay_rate
            )
            self.set_public_reputation(self._public_reputation + int(change))

        if self._decay_timer >= self._decay_interval:
            self._decay_timer = 0.0

            min_threshold = (
                self.ranks[0].threshold if self.ranks else float("inf")
            )

            for npc_id in list(self.members):
                rep = self.get_reputation(npc_id)

                if rep < min_threshold:
                    self.remove_member(npc_id)

    def _populate_from_model(self, model: FactionModel) -> None:
        self.slug = model.slug
        self.kind = model.kind
        self.alignment = model.alignment
        self.badge_id = model.badge_id
        self.leader_char = model.leader_char
        self.ranks = model.ranks
        self.members = model.members
        self.reputation = model.reputation
        self.relations = model.relations
        self._public_reputation = model.public_reputation

    def set_rank(self, npc_id: str, rank_title: str) -> None:
        self._rank_cache[npc_id] = rank_title
        logger.info(
            f"[Faction] {npc_id} assigned rank '{rank_title}' in faction '{self.slug}'"
        )

    def get_rank_for_reputation(self, rep: int) -> str | None:
        for rank in reversed(self.ranks):
            if rep >= rank.threshold:
                return rank.title
        return None

    def get_current_rank(self, npc_id: str) -> str | None:
        if npc_id in self._rank_cache:
            return self._rank_cache[npc_id]
        rep = self.get_reputation(npc_id)
        rank = self.get_rank_for_reputation(rep)
        if rank:
            self._rank_cache[npc_id] = rank
        return rank

    def get_relation(self, other_id: str) -> FactionRelationStatus:
        return self.relations.get(other_id, FactionRelationStatus.UNKNOWN)

    def is_ally(self, other_id: str) -> bool:
        return self.get_relation(other_id) == FactionRelationStatus.ALLY

    def set_relation(
        self, other_id: str, status: FactionRelationStatus
    ) -> None:
        previous = self.relations.get(other_id)
        self.relations[other_id] = status
        if previous != status:
            self.on_relation_changed(other_id, previous, status)

    def on_relation_changed(
        self,
        other_id: str,
        old_status: FactionRelationStatus | None,
        new_status: FactionRelationStatus,
    ) -> None:
        logger.info(
            f"Faction {self.slug} changed relation with {other_id} "
            f"from {old_status} to {new_status}"
        )
        if self._event_bus:
            self._event_bus.publish(
                FactionEvent.RELATION_CHANGED.value,
                faction_slug=self.slug,
                other_faction_slug=other_id,
                old_status=old_status,
                new_status=new_status,
            )

    def modify_reputation(self, npc_id: str, amount: int) -> None:
        self.reputation[npc_id] = self.reputation.get(npc_id, 0) + amount
        self._rank_cache.pop(npc_id, None)

    def get_reputation(self, npc_id: str) -> int:
        return self.reputation.get(npc_id, 0)

    def add_member(self, npc_id: str) -> None:
        if npc_id not in self.members:
            self.members.append(npc_id)
            self.on_member_joined(npc_id)

    def on_member_joined(self, npc_id: str) -> None:
        logger.info(f"{npc_id} joined faction {self.slug}")
        if self._event_bus:
            self._event_bus.publish(
                FactionEvent.MEMBER_JOINED.value,
                faction_slug=self.slug,
                npc_id=npc_id,
            )

    def remove_member(self, npc_id: str) -> None:
        if npc_id in self.members:
            self.members.remove(npc_id)
            self.on_member_removed(npc_id)

    def on_member_removed(self, npc_id: str) -> None:
        logger.info(f"{npc_id} left faction {self.slug}")
        if self._event_bus:
            self._event_bus.publish(
                FactionEvent.MEMBER_REMOVED.value,
                faction_slug=self.slug,
                npc_id=npc_id,
            )

    def has_member(self, npc_id: str) -> bool:
        return npc_id in self.members

    def evaluate_rank_change(
        self, npc_id: str, game_variables: GameVariablesManager
    ) -> str | None:
        rep = self.get_reputation(npc_id)
        desired_rank = self.get_rank_for_reputation(rep)
        current_rank = self.get_current_rank(npc_id)

        if desired_rank and desired_rank != current_rank:
            if self.can_be_promoted(npc_id, game_variables):
                self.on_promotion(npc_id, desired_rank)
            elif current_rank is not None:
                self.on_degradation(npc_id, current_rank, desired_rank)
            return desired_rank
        return None

    def on_promotion(self, npc_id: str, new_rank: str) -> None:
        self.set_rank(npc_id, new_rank)
        logger.info(f"{npc_id} promoted to {new_rank} in faction {self.slug}")
        if self._event_bus:
            self._event_bus.publish(
                FactionEvent.PROMOTED.value,
                faction_slug=self.slug,
                npc_id=npc_id,
                new_rank=new_rank,
                reputation=self.get_reputation(npc_id),
                power_level=self.power_level,
            )

    def on_degradation(
        self, npc_id: str, old_rank: str, new_rank: str
    ) -> None:
        self.set_rank(npc_id, new_rank)
        logger.info(
            f"{npc_id} demoted from {old_rank} to {new_rank} in faction {self.slug}"
        )
        if self._event_bus:
            self._event_bus.publish(
                FactionEvent.DEMOTED.value,
                faction_slug=self.slug,
                npc_id=npc_id,
                old_rank=old_rank,
                new_rank=new_rank,
                reputation=self.get_reputation(npc_id),
                power_level=self.power_level,
            )

    def can_be_promoted(
        self,
        npc_id: str,
        variable_manager: GameVariablesManager,
    ) -> bool:
        rep = self.get_reputation(npc_id)

        for rank in self.ranks:
            req = rank.requirement

            if rep >= rank.threshold:
                if req and req.variables:
                    if not variable_manager.check_conditions(req.variables):
                        continue
                return True

        return False

    def calculate_power_level(self, multiplier: int = 10) -> int:
        """
        Calculates the faction's power level based on the number of members
        and the sum of their individual reputations.

        This method provides a dynamic assessment of the faction's strength,
        reflecting both the quantity and quality (via reputation) of its
        members. The multiplier for the number of members can be adjusted
        to balance the impact of member count versus individual reputation.

        Returns:
            int: The calculated power level of the faction. Returns a minimum of 0.
        """
        num_members = len(self.members)
        total_reputation = sum(
            self.reputation.get(member_slug, 0) for member_slug in self.members
        )
        calculated_power = total_reputation + (num_members * multiplier)
        return max(0, calculated_power)

    @property
    def power_level(self) -> int:
        return self.calculate_power_level()

    def set_public_reputation(self, value: int) -> None:
        bounded_value = max(0, min(value, self.MAX_PUBLIC_REPUTATION))
        self._public_reputation = bounded_value

    @property
    def public_reputation(self) -> int:
        return self._public_reputation

    def from_save_data(
        self,
        members_data: Mapping[str, Any],
        public_reputation: int = 0,
        relations: Mapping[str, str] | None = None,
    ) -> None:
        self._public_reputation = public_reputation

        for npc_slug, npc_data in members_data.items():
            reputation = npc_data.get("reputation", 0)
            is_member = npc_data.get("is_member", False)

            self.reputation[npc_slug] = reputation

            if is_member:
                self.add_member(npc_slug)
            else:
                self.remove_member(npc_slug)

            logger.debug(
                f"[Faction] Loaded data for NPC '{npc_slug}': "
                f"reputation={reputation}, is_member={is_member}"
            )

        self.relations.clear()
        if relations:
            for slug, status_str in relations.items():
                try:
                    self.relations[slug] = FactionRelationStatus[status_str]
                except KeyError:
                    logger.warning(
                        f"[Faction] Unknown relation status '{status_str}' for faction '{slug}'"
                    )

    def to_save_data(self, npc_slugs: list[str]) -> dict[str, Any] | None:
        members_data: dict[str, Any] = {}

        for npc_slug in npc_slugs:
            reputation = self.get_reputation(npc_slug)
            is_member = self.has_member(npc_slug)

            if reputation != 0 or is_member:
                members_data[npc_slug] = {
                    "reputation": reputation,
                    "is_member": is_member,
                }

        if (
            not members_data
            and self.public_reputation == 0
            and not self.relations
        ):
            return None

        return {
            "members": members_data,
            "public_reputation": self.public_reputation,
            "relations": {
                slug: status.name for slug, status in self.relations.items()
            },
        }
