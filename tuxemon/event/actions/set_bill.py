# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T

logger = logging.getLogger(__name__)


@final
@dataclass
class SetBillAction(EventAction):
    """
    Set a bill.

    Script usage:
        .. code-block::

            set_money <slug>,<bill_slug>,[amount]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        bill_slug: Slug of the bill.
        amount: Amount of money (>= 0) (default 0)
    """

    name = "set_bill"
    character: str
    bill_slug: str
    amount: Optional[int] = None

    def start(self) -> None:
        character = get_npc(self.session, self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return

        if not T.has_translation("en_US", self.bill_slug):
            logger.error(f"Please add {self.bill_slug} to the en_US base.po")

        amount = 0 if self.amount is None else self.amount
        if amount < 0:
            raise AttributeError(f"{amount} must be >= 0")
        else:
            money_manager = character.money_controller.money_manager
            money_manager.add_entry(self.bill_slug, amount)
            logger.info(f"{character.name}'s have {amount}")
