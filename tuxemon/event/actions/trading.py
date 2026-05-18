# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.database.runtime import db
from tuxemon.event.eventaction import EventAction
from tuxemon.tools import get_valid_uuid
from tuxemon.trade_manager import TradeResult

if TYPE_CHECKING:
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


@final
@dataclass
class TradingAction(EventAction):
    """
    Select a monster in the player party and trade.

    Script usage:
        .. code-block::

            trading <variable>,<added>

    Script parameters:
        variable: Name of the variable where to store the monster id (removed).
        added: Slug monster or Name of the variable where to store the monster
            id (added).

    eg. "trading name_variable,apeoro"
    eg. "trading name_variable,name_variable"
    """

    name = "trading"
    variable: str
    added: str

    def start(self, session: Session) -> None:
        player = session.player
        player_monster_id = get_valid_uuid(
            player.game_variables, self.variable
        )
        if player_monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID

        player_monster = session.client.get_monster_by_iid(player_monster_id)
        if player_monster is None:
            logger.error("Player's monster not found.")
            self.stop()
            return

        if self.added in db.database["monster"]:
            # Trade for a new monster from the database
            result = session.client.trade_manager.execute_scripted_trade(
                player_monster, self.added
            )

            if result == TradeResult.SUCCESS:
                logger.info("Scripted trade completed successfully.")
                session.client.push_state(
                    "TradingTransition",
                    sent_monster=player_monster.slug,
                    received_monster=self.added,
                )
            elif result == TradeResult.NOT_FOUND:
                logger.error("Player's monster not found in party.")
        else:
            # Trade for an existing monster from another party
            other_monster_id = get_valid_uuid(
                player.game_variables, self.added
            )
            if other_monster_id is None:
                logger.info(
                    f"No valid monster selected for variable '{self.added}'"
                )
                self.stop()
                return  # Exit early if no valid UUID

            other_monster = session.client.get_monster_by_iid(other_monster_id)
            if other_monster is None:
                logger.error("Other monster not found.")
                self.stop()
                return

            result = session.client.trade_manager.execute_trade(
                player_monster, other_monster
            )

            if result == TradeResult.SUCCESS:
                logger.info("Trade completed successfully!")
                session.client.push_state(
                    "TradingTransition",
                    sent_monster=player_monster.slug,
                    received_monster=other_monster.slug,
                )
            elif result == TradeResult.SAME_OWNER:
                logger.error("You can't trade with yourself.")
            elif result == TradeResult.NOT_FOUND:
                logger.error("One of the monsters wasn't found in the party.")
