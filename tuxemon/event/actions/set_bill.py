# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetBillAction(EventAction):
    """
    Initializes or updates a bill for a character, including its amount,
    interest rate, late fee and share rate.

    Script usage:
        .. code-block::

            set_bill <character>,<bill_slug>[,amount][,interest_rate][,late_fee][,share_rate]

    Script parameters:
        character: "player" or the slug of an NPC (e.g. "npc_maple").
        bill_slug: identifier for the bill (must be translated in en_US base.po).
        amount: initial amount of the bill (optional, defaults to 0).
        interest_rate: interest rate applied to the bill (optional, e.g. 0.1 for 10%).
        late_fee: flat fee added to the bill when triggered (optional, eg. 10).
        share_rate: percentage of battle earnings automatically applied to the bill
            (optional, e.g. 0.2 for 20%).

    Examples:
        set_bill player,bill_cathedral,100,0.1,50,0.5
        set_bill npc_maple,bill_rent,,0.05,25,0.2

    Notes:
        - Interest and late fee are stored but not automatically applied.
        - Use separate actions to trigger interest or fee accumulation.
        - Amount must be non-negative.
    """

    name = "set_bill"
    character: str
    bill_slug: str
    amount: int | None = None
    interest_rate: float | None = None
    late_fee: int | None = None
    share_rate: float | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found.")
            self.stop()
            return

        if not T.has_translation("en_US", self.bill_slug):
            logger.warning(
                f"Missing translation for bill_slug '{self.bill_slug}' in en_US base.po."
            )

        amount = 0 if self.amount is None else self.amount
        if amount < 0:
            raise ValueError(f"Amount must be >= 0, got {amount}.")

        money_manager = character.money_controller.money_manager
        money_manager.set_bill(
            bill_name=self.bill_slug,
            amount=amount,
            interest_rate=self.interest_rate,
            late_fee=self.late_fee,
            share_rate=self.share_rate,
        )

        logger.info(
            f"Set bill '{self.bill_slug}' for {character.name} with amount {amount}, "
            f"interest rate {self.interest_rate}, and late fee {self.late_fee}."
        )
