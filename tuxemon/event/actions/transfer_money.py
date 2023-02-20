# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class MoneyMathAction(EventAction):
    """
    Perform a mathematical transaction on the player's money.

    Script usage:
        .. code-block::

            transfer_money <transaction>,<amount>[,slug]

    Script parameters:
        transaction: Operator symbol.
        amount: amount of money.
        slug: Slug name (e.g. NPC, etc.)
        eg: +,100,mom (player gets 100 from mom)
        eg: -,100,mom (mom gets 100 from player)
        eg: +,100 (player gets 100)

    """

    name = "transfer_money"
    transaction: str
    amount: int
    slug: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player

        # Read the parameters
        transaction = self.transaction
        amount = self.amount

        wallet_player = player.money.get("player")

        # Perform the transaction on the slug
        # from the slug wallet to the player, included check if it's None
        if transaction == "+":
            player.money["player"] = wallet_player + amount
            if self.slug is not None:
                wallet_npc = player.money.get(self.slug)
                if wallet_npc is None:
                    player.money[self.slug] = amount * -1
                else:
                    player.money[self.slug] = wallet_npc - amount
        # from the player wallet to the slug
        elif transaction == "-":
            player.money["player"] = wallet_player - amount
            if self.slug is not None:
                wallet_npc = player.money.get(self.slug)
                if wallet_npc is None:
                    player.money[self.slug] = amount
                else:
                    player.money[self.slug] = wallet_npc + amount
        else:
            raise ValueError(f"invalid transaction type {transaction}")
