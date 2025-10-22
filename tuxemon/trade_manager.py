# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon.db import Acquisition, SeenStatus
from tuxemon.event import get_event_bus, get_monster_by_iid
from tuxemon.monster import Monster
from tuxemon.time_handler import today_ordinal

if TYPE_CHECKING:
    from tuxemon.npc import NPC
    from tuxemon.session import Session

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
    expires_at: Optional[datetime] = None


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
    def __init__(self) -> None:
        self.global_trade_log: list[TradeRecord] = []
        self.pending_offers: list[TradeOffer] = []
        self.event_bus = get_event_bus()

    def execute_trade(
        self, monster_a: Monster, monster_b: Monster
    ) -> TradeResult:
        player_a = monster_a.get_owner()
        player_b = monster_b.get_owner()

        if player_a == player_b:
            logger.warning(
                "Attempted to trade two monsters from the same owner."
            )
            return TradeResult.SAME_OWNER

        try:
            slot_a = player_a.party.monsters.index(monster_a)
            slot_b = player_b.party.monsters.index(monster_b)
        except ValueError:
            logger.error(
                "One of the monsters was not found in its owner's party during trade."
            )
            return TradeResult.NOT_FOUND

        player_a.party.remove_monster(monster_a)
        player_b.party.remove_monster(monster_b)

        player_a.party.insert_monster_to_party(monster_b, slot_a)
        player_b.party.insert_monster_to_party(monster_a, slot_b)

        monster_a.set_owner(player_b)
        monster_b.set_owner(player_a)

        monster_a.set_acquisition(Acquisition.TRADED)
        monster_b.set_acquisition(Acquisition.TRADED)

        player_a.tuxepedia.add_entry(monster_b.slug, SeenStatus.caught)
        player_b.tuxepedia.add_entry(monster_a.slug, SeenStatus.caught)

        record_a = self._create_trade_record(
            from_player=player_a,
            to_player=player_b,
            given_monster=monster_a,
            received_monster=monster_b,
        )
        record_b = self._create_trade_record(
            from_player=player_b,
            to_player=player_a,
            given_monster=monster_b,
            received_monster=monster_a,
        )

        self.event_bus.publish("trade_completed", [record_a, record_b])

        self.global_trade_log.extend([record_a, record_b])

        logger.info(f"{player_a.name} welcomes {monster_b.name}!")
        logger.info(f"{player_b.name} welcomes {monster_a.name}!")

        return TradeResult.SUCCESS

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

    def execute_scripted_trade(
        self, player_monster: Monster, added_slug: str
    ) -> TradeResult:
        player = player_monster.get_owner()

        new_monster = Monster.spawn_base(added_slug, player_monster.level)
        new_monster.set_capture(today_ordinal())
        new_monster.set_acquisition(Acquisition.TRADED)

        if not player.party.replace_monster(player_monster, new_monster):
            logger.error("Player's monster not found in party.")
            return TradeResult.NOT_FOUND

        player.tuxepedia.add_entry(new_monster.slug, SeenStatus.caught)

        record = TradeRecord(
            from_player=player.name,
            to_player="NPC",
            from_player_id=player.instance_id,
            to_player_id=UUID(int=0),
            monster_given=player_monster.slug,
            monster_received=added_slug,
            monster_given_id=player_monster.instance_id,
            monster_received_id=new_monster.instance_id,
        )

        self.global_trade_log.append(record)
        self.event_bus.publish("trade_completed", [record])

        logger.info(
            f"{player.name} traded {player_monster.name} for {new_monster.name} (scripted trade)."
        )
        return TradeResult.SUCCESS

    def propose_trade(
        self, proposing_monster: Monster, requested_monster: Monster
    ) -> TradeResult:
        """Creates a trade offer for a monster and adds it to the list of pending offers."""
        proposing_player = proposing_monster.get_owner()
        receiving_player = requested_monster.get_owner()

        if proposing_player == receiving_player:
            logger.warning(
                f"Attempted to propose a trade with a monster from the same owner: {proposing_player.name}."
            )
            return TradeResult.SAME_OWNER

        try:
            proposing_player.party.monsters.index(proposing_monster)
            receiving_player.party.monsters.index(requested_monster)
        except ValueError:
            logger.error(
                "One of the monsters was not found in its owner's party during trade proposal."
            )
            return TradeResult.NOT_FOUND

        new_offer = TradeOffer(
            proposing_player_id=proposing_player.instance_id,
            proposing_monster_id=proposing_monster.instance_id,
            receiving_player_id=receiving_player.instance_id,
            requested_monster_id=requested_monster.instance_id,
        )

        self.pending_offers.append(new_offer)
        logger.info(
            f"Trade offer from {proposing_player.name} to {receiving_player.name} proposed."
        )
        self.event_bus.publish("trade_offer_proposed", new_offer)
        return TradeResult.SUCCESS

    def accept_trade(self, session: Session, offer_id: UUID) -> TradeResult:
        """Accepts a pending trade offer, executing the trade if valid."""
        offer: Optional[TradeOffer] = None
        try:
            offer = next(
                o for o in self.pending_offers if o.offer_id == offer_id
            )
        except StopIteration:
            logger.error(f"Trade offer with ID {offer_id} not found.")
            return TradeResult.NOT_FOUND

        if offer.expires_at and datetime.now(timezone.utc) > offer.expires_at:
            logger.warning(f"Trade offer {offer_id} has expired.")
            self.pending_offers.remove(offer)
            return TradeResult.EXPIRED

        proposing_monster = get_monster_by_iid(
            session, offer.proposing_monster_id
        )
        requested_monster = get_monster_by_iid(
            session, offer.requested_monster_id
        )

        if not proposing_monster or not requested_monster:
            logger.error(
                "One or both monsters in the trade offer no longer exist."
            )
            self.pending_offers.remove(offer)
            return TradeResult.NOT_FOUND

        if (
            proposing_monster.get_owner().instance_id
            != offer.proposing_player_id
            or requested_monster.get_owner().instance_id
            != offer.receiving_player_id
        ):
            logger.error("Trade offer invalid: monster ownership has changed.")
            self.pending_offers.remove(offer)
            return TradeResult.NOT_FOUND

        result = self.execute_trade(proposing_monster, requested_monster)

        if result == TradeResult.SUCCESS:
            self.pending_offers.remove(offer)
            logger.info(f"Trade offer {offer_id} accepted and completed.")
        else:
            logger.error(
                f"Trade offer {offer_id} failed to complete with result: {result.value}."
            )

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

    def get_trade_history(
        self, player_name: Optional[str] = None
    ) -> list[str]:
        records = self.global_trade_log
        if player_name:
            records = [
                r
                for r in records
                if r.from_player == player_name or r.to_player == player_name
            ]
        return [
            f"{r.timestamp.strftime('%Y-%m-%d %H:%M')} — {r.from_player} traded {r.monster_given} for {r.monster_received} with {r.to_player}"
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
