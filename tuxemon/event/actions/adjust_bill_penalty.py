# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
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
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return

        money_manager = character.money_controller.money_manager
        if self.method == "interest":
            money_manager.apply_interest_to_bill(self.bill_slug)
        elif self.method == "fee":
            money_manager.apply_late_fee_to_bill(self.bill_slug)
        else:
            raise ValueError(
                f"Invalid method '{self.method}': must be 'interest' or 'fee'"
            )
