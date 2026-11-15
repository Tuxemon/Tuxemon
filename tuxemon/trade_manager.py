# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from tuxemon.db import Acquisition
from tuxemon.event import get_event_bus
from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.npc_manager import NPCManager

logger = logging.getLogger(__name__)


class TradeResult(Enum):
    SUCCESS = "success"
    SAME_OWNER = "same_owner"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"


@dataclass
class TradeOffer:
    proposing_player_id: UUID
    proposing_monster_id: UUID
    receiving_player_id: UUID
    requested_monster_id: UUID
    offer_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime | None = None


@dataclass
class TradeRecord:
    from_player: str
    to_player: str
    from_player_id: UUID
    to_player_id: UUID
    monster_given: str
    monster_received: str
    monster_given_id: UUID
    monster_received_id: UUID
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, str]:
        return {
            "from_player": self.from_player,
            "to_player": self.to_player,
            "from_player_id": str(self.from_player_id),
            "to_player_id": str(self.to_player_id),
            "monster_given": self.monster_given,
            "monster_received": self.monster_received,
            "monster_given_id": str(self.monster_given_id),
            "monster_received_id": str(self.monster_received_id),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> TradeRecord:
        return cls(
            from_player=data["from_player"],
            to_player=data["to_player"],
            from_player_id=UUID(data["from_player_id"]),
            to_player_id=UUID(data["to_player_id"]),
            monster_given=data["monster_given"],
            monster_received=data["monster_received"],
            monster_given_id=UUID(data["monster_given_id"]),
            monster_received_id=UUID(data["monster_received_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class TradeManager:
    def __init__(self, npc_manager: NPCManager) -> None:
        self.npc_manager = npc_manager
        self.global_trade_log: list[TradeRecord] = []
        self.pending_offers: list[TradeOffer] = []
        self.event_bus = get_event_bus()

    def _find_owner(self, monster: Monster) -> NPC | None:
        return self.npc_manager.get_monster_owner(monster)

    def _require_owners(
        self, a: NPC | None, b: NPC | None
    ) -> tuple[NPC, NPC] | TradeResult:
        """Validate owners and return typed NPCs."""
        if a is None or b is None:
            return TradeResult.NOT_FOUND
        if a is b:
            return TradeResult.SAME_OWNER
        return (a, b)

    def _find_party_slot(self, player: NPC, monster: Monster) -> int | None:
        try:
            return player.party.monsters.index(monster)
        except ValueError:
            return None

    def _swap_monsters(
        self,
        player_a: NPC,
        player_b: NPC,
        monster_a: Monster,
        monster_b: Monster,
        slot_a: int,
        slot_b: int,
    ) -> None:
        player_a.party.remove_monster(monster_a)
        player_b.party.remove_monster(monster_b)

        player_a.party.insert_monster_to_party(monster_b, slot_a)
        player_b.party.insert_monster_to_party(monster_a, slot_b)

    def _award_tuxepedia(
        self,
        player_a: NPC,
        player_b: NPC,
        monster_a: Monster,
        monster_b: Monster,
    ) -> None:
        player_a.tuxepedia.register_caught(monster_b.slug)
        player_b.tuxepedia.register_caught(monster_a.slug)

    def _create_trade_record(
        self,
        from_player: NPC,
        to_player: NPC,
        given_monster: Monster,
        received_monster: Monster,
    ) -> TradeRecord:
        return TradeRecord(
            from_player=from_player.name,
            to_player=to_player.name,
            from_player_id=from_player.instance_id,
            to_player_id=to_player.instance_id,
            monster_given=given_monster.slug,
            monster_received=received_monster.slug,
            monster_given_id=given_monster.instance_id,
            monster_received_id=received_monster.instance_id,
        )

    def _create_trade_pair(
        self,
        player_a: NPC,
        player_b: NPC,
        monster_a: Monster,
        monster_b: Monster,
    ) -> list[TradeRecord]:
        return [
            self._create_trade_record(
                player_a, player_b, monster_a, monster_b
            ),
            self._create_trade_record(
                player_b, player_a, monster_b, monster_a
            ),
        ]

    def execute_trade(
        self, monster_a: Monster, monster_b: Monster
    ) -> TradeResult:
        owner_a = self._find_owner(monster_a)
        owner_b = self._find_owner(monster_b)

        owners = self._require_owners(owner_a, owner_b)
        if isinstance(owners, TradeResult):
            return owners

        player_a, player_b = owners  # fully typed NPCs

        slot_a = self._find_party_slot(player_a, monster_a)
        slot_b = self._find_party_slot(player_b, monster_b)
        if slot_a is None or slot_b is None:
            return TradeResult.NOT_FOUND

        self._swap_monsters(
            player_a, player_b, monster_a, monster_b, slot_a, slot_b
        )

        monster_a.set_acquisition(Acquisition.TRADED)
        monster_b.set_acquisition(Acquisition.TRADED)

        self._award_tuxepedia(player_a, player_b, monster_a, monster_b)

        records = self._create_trade_pair(
            player_a, player_b, monster_a, monster_b
        )
        self.global_trade_log.extend(records)
        self.event_bus.publish("trade_completed", records)

        return TradeResult.SUCCESS

    def execute_scripted_trade(
        self, player_monster: Monster, added_slug: str
    ) -> TradeResult:
        owner = self._find_owner(player_monster)
        if owner is None:
            return TradeResult.NOT_FOUND

        new_monster = Monster.spawn_base(added_slug, player_monster.level)
        new_monster.set_acquisition(Acquisition.TRADED)

        if not owner.party.replace_monster(player_monster, new_monster):
            return TradeResult.NOT_FOUND

        owner.tuxepedia.register_caught(new_monster.slug)

        record = TradeRecord(
            from_player=owner.name,
            to_player="NPC",
            from_player_id=owner.instance_id,
            to_player_id=UUID(int=0),
            monster_given=player_monster.slug,
            monster_received=added_slug,
            monster_given_id=player_monster.instance_id,
            monster_received_id=new_monster.instance_id,
        )

        self.global_trade_log.append(record)
        self.event_bus.publish("trade_completed", [record])

        return TradeResult.SUCCESS

    def propose_trade(
        self, proposing_monster: Monster, requested_monster: Monster
    ) -> TradeResult:
        owner_a = self._find_owner(proposing_monster)
        owner_b = self._find_owner(requested_monster)

        owners = self._require_owners(owner_a, owner_b)
        if isinstance(owners, TradeResult):
            return owners

        player_a, player_b = owners

        if (
            self._find_party_slot(player_a, proposing_monster) is None
            or self._find_party_slot(player_b, requested_monster) is None
        ):
            return TradeResult.NOT_FOUND

        offer = TradeOffer(
            proposing_player_id=player_a.instance_id,
            proposing_monster_id=proposing_monster.instance_id,
            receiving_player_id=player_b.instance_id,
            requested_monster_id=requested_monster.instance_id,
        )

        self.pending_offers.append(offer)
        self.event_bus.publish("trade_offer_proposed", offer)
        return TradeResult.SUCCESS

    def accept_trade(self, offer_id: UUID) -> TradeResult:
        offer = next(
            (o for o in self.pending_offers if o.offer_id == offer_id), None
        )
        if offer is None:
            return TradeResult.NOT_FOUND

        if offer.expires_at and datetime.now(timezone.utc) > offer.expires_at:
            self.pending_offers.remove(offer)
            return TradeResult.EXPIRED

        proposing_monster = self.npc_manager.get_monster_by_iid(
            offer.proposing_monster_id
        )
        requested_monster = self.npc_manager.get_monster_by_iid(
            offer.requested_monster_id
        )

        if proposing_monster is None or requested_monster is None:
            self.pending_offers.remove(offer)
            return TradeResult.NOT_FOUND

        owner_a = self._find_owner(proposing_monster)
        owner_b = self._find_owner(requested_monster)

        if owner_a is None or owner_b is None:
            self.pending_offers.remove(offer)
            return TradeResult.NOT_FOUND

        player_a, player_b = owner_a, owner_b

        if (
            player_a.instance_id != offer.proposing_player_id
            or player_b.instance_id != offer.receiving_player_id
        ):
            self.pending_offers.remove(offer)
            return TradeResult.NOT_FOUND

        result = self.execute_trade(proposing_monster, requested_monster)

        if result == TradeResult.SUCCESS:
            self.pending_offers.remove(offer)

        return result

    def was_traded_with_player(self, player_name: str) -> bool:
        return any(
            record.from_player == player_name
            or record.to_player == player_name
            for record in self.global_trade_log
        )

    def was_traded_for_monster(self, monster_slug: str) -> bool:
        return any(
            record.monster_given == monster_slug
            or record.monster_received == monster_slug
            for record in self.global_trade_log
        )

    def get_trade_history(self, player_name: str | None = None) -> list[str]:
        records = self.global_trade_log
        if player_name is not None:
            records = [
                r
                for r in records
                if r.from_player == player_name or r.to_player == player_name
            ]
        return [
            f"{r.timestamp.strftime('%Y-%m-%d %H:%M')} — "
            f"{r.from_player} traded {r.monster_given} for "
            f"{r.monster_received} with {r.to_player}"
            for r in records
        ]

    def save_log(self) -> Mapping[str, Any]:
        return {
            "trade_history": [
                record.to_dict() for record in self.global_trade_log
            ]
        }

    def load_log(self, data: Mapping[str, Any]) -> None:
        trade_data = data.get("trade_history", [])
        self.global_trade_log = [TradeRecord.from_dict(r) for r in trade_data]


def on_trade_completed(records: list[TradeRecord]) -> None:
    for record in records:
        logger.info(
            f"{record.from_player} traded {record.monster_given} for {record.monster_received} with {record.to_player}"
        )


# trade_manager = TradeManager()
# trade_manager.event_bus.subscribe("trade_completed", on_trade_completed)
