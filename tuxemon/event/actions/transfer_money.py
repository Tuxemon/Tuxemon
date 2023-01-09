# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class MoneyMathAction(EventAction):
    """
    Perform a mathematical transaction on the player's money.

    Script usage:
        .. code-block::

            transfer_money <transaction>,<amount>,<slug>

    Script parameters:
        transaction: Operator symbol.
        amount: amount of money.
        slug: Slug name (e.g. NPC, etc.)
        eg: +,100,mom (player gets 100 from mom)
        eg: -,100,mom (mom gets 100 from player)

    """

    name = "transfer_money"
    transaction: str
    amount: int
    slug: str

    def start(self) -> None:
        player = self.session.player

        # Read the parameters
        transaction = self.transaction
        amount = self.amount
        destination = self.slug

        # Data
        wallet_player = player.money.get("player")
        wallet_slug = player.money.get(destination)

        # Perform the transaction on the slug
        # from the slug wallet to the player, included check if it's None
        if transaction == "+":
            if wallet_player is None:
                own = 0
                player.money["player"] = int(own) + amount
            else:
                player.money["player"] = wallet_player + amount
            if wallet_slug is None:
                value = 0
                player.money[destination] = int(value) - amount
            else:
                player.money[destination] = int(wallet_slug) - amount
        # from the player wallet to the slug
        elif transaction == "-":
            if wallet_player is None:
                own = 0
                player.money["player"] = int(own) - amount
            else:
                player.money["player"] = wallet_player - amount
            if wallet_slug is None:
                value = 0
                player.money[destination] = int(value) + amount
            else:
                player.money[destination] = int(wallet_slug) + amount
        else:
            raise ValueError(f"invalid transaction type {transaction}")
