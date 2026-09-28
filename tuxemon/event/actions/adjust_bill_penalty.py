# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class AdjustBillPenaltyAction(EventAction):
    """
    Applies a penalty to a bill for a character — either interest or late fee.

    Script usage:
        .. code-block::

            adjust_bill_penalty <character_slug>,<bill_slug>,<method>

    Script parameters:
        character_slug: Slug of the character (e.g. "player", "npc_maple").
        bill_slug: Slug of the bill to modify.
        method: Either "interest" or "fee".

    Examples:
        adjust_bill_penalty player,electric_bill,interest
        adjust_bill_penalty npc_maple,rent,fee
    """

    name = "adjust_bill_penalty"
    character: str
    bill_slug: str
    method: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found")
            self.stop()
            return

        money_manager = character.money_controller.money_manager

        bill = money_manager.get_bill(self.bill_slug)
        if bill is None:
            logger.error(
                f"Bill '{self.bill_slug}' not found for character '{self.character}'"
            )
            self.stop()
            return

        try:
            if self.method == "interest":
                money_manager.apply_interest_to_bill(self.bill_slug)
                action = "interest"
            elif self.method == "fee":
                money_manager.apply_late_fee_to_bill(self.bill_slug)
                action = "late fee"
            else:
                logger.error(
                    f"Invalid method '{self.method}': must be 'interest' or 'fee'"
                )
                self.stop()
                return
        except Exception as e:
            logger.error(
                f"Failed to apply {self.method} to bill '{self.bill_slug}' "
                f"for '{self.character}': {e}"
            )
            self.stop()
            return

        updated_bill = money_manager.get_bill(self.bill_slug)
        if updated_bill:
            logger.debug(
                f"Applied {action} to bill '{self.bill_slug}' for {character.name}. "
                f"New amount: {updated_bill.amount}"
            )
        else:
            logger.debug(
                f"Applied {action} to bill '{self.bill_slug}' for {character.name}. "
                f"The bill has been fully paid and removed."
            )
