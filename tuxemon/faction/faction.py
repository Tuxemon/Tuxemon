# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Optional

from tuxemon.db import (
    FactionAlignment,
    FactionKind,
    FactionModel,
    FactionRelationStatus,
    RankStep,
    db,
)
from tuxemon.locale import T

logger = logging.getLogger(__name__)


class Faction:
    """
    Represents a faction within the Tuxemon game world.

    This class manages all aspects of a faction, including its identity,
    relationships with other factions, and the status of its members.
    It handles reputation tracking for individual NPCs, determines their ranks
    within the faction, and manages their membership.
    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}
        self._rank_cache: dict[str, str] = {}
        self.slug: str = ""
        self.name: str = ""
        self.description: str = ""
        self.kind: Optional[FactionKind] = None
        self.alignment: Optional[FactionAlignment] = None
        self.badge_id: Optional[str] = None
        self.leader_char: Optional[str] = None
        self.ranks: list[RankStep] = []
        self.members: list[str] = []
        self.reputation: dict[str, int] = {}
        self.relations: dict[str, FactionRelationStatus] = {}

    def load(self, slug: str) -> None:
        """
        Loads and sets faction from the db using a slug.
        """
        results = FactionModel.lookup(slug, db)
        self._populate_from_model(results)

    @classmethod
    def load_from_db(cls, slug: str) -> Faction:
        """
        Factory method to load and return a Faction instance from the db.
        """
        results = FactionModel.lookup(slug, db)
        faction = cls()
        faction._populate_from_model(results)
        return faction

    def _populate_from_model(self, model: FactionModel) -> None:
        self.slug = model.slug
        self.name = T.translate(model.slug)
        self.description = T.translate(f"{model.slug}_description")
        self.kind = model.kind
        self.alignment = model.alignment
        self.badge_id = model.badge_id
        self.leader_char = model.leader_char
        self.ranks = model.ranks
        self.members = model.members
        self.reputation = model.reputation
        self.relations = model.relations

    def set_rank(self, npc_id: str, rank_title: str) -> None:
        self._rank_cache[npc_id] = rank_title
        logger.info(
            f"[Faction] {npc_id} assigned rank '{rank_title}' in faction '{self.slug}'"
        )

    def get_rank_for_reputation(self, rep: int) -> Optional[str]:
        for rank in reversed(self.ranks):
            if rep >= rank.threshold:
                return rank.title
        return None

    def get_current_rank(self, npc_id: str) -> Optional[str]:
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
        old_status: Optional[FactionRelationStatus],
        new_status: FactionRelationStatus,
    ) -> None:
        logger.info(
            f"Faction {self.slug} changed relation with {other_id} "
            f"from {old_status} to {new_status}"
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

    def remove_member(self, npc_id: str) -> None:
        if npc_id in self.members:
            self.members.remove(npc_id)
            self.on_member_removed(npc_id)

    def on_member_removed(self, npc_id: str) -> None:
        logger.info(f"{npc_id} left faction {self.slug}")

    def has_member(self, npc_id: str) -> bool:
        return npc_id in self.members

    def check_promotion(
        self,
        npc_id: str,
        game_variables: dict[str, Any],
    ) -> Optional[str]:
        if not self.can_be_promoted(npc_id, game_variables):
            return None

        rep = self.get_reputation(npc_id)
        current_rank = self.get_current_rank(npc_id)
        next_rank = None

        for rank in self.ranks:
            if rep >= rank.threshold:
                next_rank = rank.title
            else:
                break

        if next_rank and current_rank and next_rank != current_rank:
            self.on_promotion(npc_id, next_rank)
            return next_rank
        return None

    def check_degradation(self, npc_id: str) -> Optional[str]:
        rep = self.get_reputation(npc_id)
        current_rank = self.get_current_rank(npc_id)

        if current_rank is None:
            if self.ranks and rep >= self.ranks[0].threshold:
                return self.ranks[0].title
            return None

        for rank in reversed(self.ranks):
            if rep >= rank.threshold:
                if rank.title != current_rank:
                    self.on_degradation(npc_id, current_rank, rank.title)
                    return rank.title
                break
        return None

    def on_promotion(self, npc_id: str, new_rank: str) -> None:
        self.set_rank(npc_id, new_rank)
        logger.info(f"{npc_id} promoted to {new_rank} in faction {self.slug}")

    def on_degradation(
        self, npc_id: str, old_rank: str, new_rank: str
    ) -> None:
        self.set_rank(npc_id, new_rank)
        logger.info(
            f"{npc_id} demoted from {old_rank} to {new_rank} in faction {self.slug}"
        )

    def can_be_promoted(
        self,
        npc_id: str,
        game_variables: dict[str, Any],
    ) -> bool:
        rep = self.get_reputation(npc_id)
        for rank in self.ranks:
            req = rank.requirement
            if rep >= rank.threshold:
                if req:
                    if req.variables:
                        if not satisfies_all_requirements(
                            req.variables, game_variables
                        ):
                            continue
                return True
        return False


def satisfies_all_requirements(
    req_variables: Sequence[dict[str, Any]], game_variables: dict[str, Any]
) -> bool:
    return all(
        all(
            game_variables.get(key) == value for key, value in variable.items()
        )
        for variable in req_variables
    )
