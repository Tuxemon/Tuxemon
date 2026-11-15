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
    amount: int | None = None
    variable: str | None = None

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)

        if character is None:
            logger.error(f"Character '{self.character}' not found")
            self.stop()
            return

        player = session.player
        money_manager = character.money_controller.money_manager

        if self.amount is None:
            if self.variable:
                raw_value = player.game_variables.get(self.variable, 0)

                if isinstance(raw_value, int):
                    amount = raw_value

                elif isinstance(raw_value, float):
                    bill = money_manager.get_bill(self.bill_slug)
                    if bill is None:
                        logger.error(f"Bill '{self.bill_slug}' not found")
                        self.stop()
                        return
                    amount = int(bill.amount * raw_value)

                else:
                    raise ValueError(
                        f"Variable '{self.variable}' must be int or float, "
                        f"got {type(raw_value).__name__}"
                    )
            else:
                amount = 0
        else:
            amount = self.amount

        if not T.has_translation("en_US", self.bill_slug):
            logger.error(f"Please add {self.bill_slug} to the en_US base.po")

        try:
            if amount >= 0:
                money_manager.add_bill(self.bill_slug, amount)
            else:
                money_manager.remove_bill(self.bill_slug, -amount)
        except KeyError as e:
            logger.error(str(e))
            self.stop()
            return

        bill = money_manager.get_bill(self.bill_slug)
        new_amount = bill.amount if bill else 0

        logger.debug(
            f"Bill '{self.bill_slug}' changed by {amount}. New amount: {new_amount}"
        )
