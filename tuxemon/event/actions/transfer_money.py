# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class MoneyMathAction(EventAction):
    """
    Performs a money transaction between entities.

    Script usage:
        .. code-block::

            transfer_money <transaction>,<amount>[,slug]

    Script parameters:
        slug1: Slug name (e.g. NPC, etc.)
        transaction: Operator symbol.
        amount: amount of money.
        slug2: Slug name (e.g. NPC, etc.)

    eg: player,+,100,mom (player gets 100 from mom)
    eg: player,-,100,mom (mom gets 100 from player)
    eg: player,+,100 (player gets 100)

    """

    name = "transfer_money"
    slug1: str
    transaction: str
    amount: int
    slug2: Optional[str] = None

    def start(self) -> None:
        player = self.session.player

        # Read the parameters
        transaction = self.transaction
        amount = self.amount
        wallet_character1 = player.money.get(self.slug1, 0)

        # Perform the transaction
        if transaction == "+":
            player.money[self.slug1] = wallet_character1 + amount
            logger.info(f"{self.slug1} money increased by {amount}")
            if self.slug2 is not None:
                wallet_character2 = player.money.get(self.slug2, 0)
                _diff = wallet_character2 - amount
                diff = 0 if _diff < 0 else _diff
                player.money[self.slug2] = diff
        elif transaction == "-":
            _diff = wallet_character1 - amount
            diff = 0 if _diff < 0 else _diff
            player.money[self.slug1] = diff
            logger.info(f"{self.slug1} money decreased by {amount}")
            if self.slug2 is not None:
                wallet_character2 = player.money.get(self.slug2, 0)
                player.money[self.slug2] = wallet_character2 + amount
        else:
            raise ValueError(f"Invalid transaction type {transaction}")
