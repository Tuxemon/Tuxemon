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
class ModifyBillAction(EventAction):
    """
    Add or remove an amount of money from a bill (slug).

    Script usage:
        .. code-block::

            modify_bill <slug>,<bill_slug>,[amount][,variable]

    Script parameters:
        slug: Either "player" or character slug name (e.g. "npc_maple").
        bill_slug: Slug of the bill.
        amount: Amount of money to add/remove (-/+)
        variable: Name of the variable where to store the amount.

    eg. "modify_bill player,bill_slug,-50"
    eg. "modify_bill player,bill_slug,,name_variable"

    """

    name = "modify_bill"
    character: str
    bill_slug: str
    amount: Optional[int] = None
    variable: Optional[str] = None

    def start(self) -> None:
        character = get_npc(self.session, self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return

        player = self.session.player
        money_manager = character.money_controller.money_manager
        if self.amount is None:
            if self.variable:
                _amount = player.game_variables.get(self.variable, 0)
                if isinstance(_amount, int):
                    amount = int(_amount)
                elif isinstance(_amount, float):
                    _value = float(_amount)
                    _wallet = money_manager.get_bill(self.bill_slug)
                    amount = int(_wallet.amount * _value)
                else:
                    raise ValueError("It must be float or int")
            else:
                amount = 0
        else:
            amount = self.amount

        if not T.has_translation("en_US", self.bill_slug):
            logger.error(f"Please add {self.bill_slug} to the en_US base.po")

        bill_amount = money_manager.get_bill(self.bill_slug).amount
        if bill_amount <= 0:
            logger.error(f"Bill '{self.bill_slug}' doesn't exist")
            return
        if amount >= 0:
            money_manager.add_bill(self.bill_slug, amount)
        else:
            money_manager.remove_bill(self.bill_slug, amount)
