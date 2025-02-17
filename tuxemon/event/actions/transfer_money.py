# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class TransferMoneyAction(EventAction):
    """
    Transfer money between entities.
    Both entities needs to have a wallet.

    Script usage:
        .. code-block::

            transfer_money <slug1>,<amount>,<slug2>

    Script parameters:
        slug1: Slug name (e.g. NPC, etc.)
        amount: amount of money.
        slug2: Slug name (e.g. NPC, etc.)

    eg: player,100,mom (player transfer 100 to mom)

    """

    name = "transfer_money"
    slug1: str
    amount: int
    slug2: str

    def start(self) -> None:
        client = self.session.client
        player = self.session.player
        wallet_char1 = player.money.get(self.slug1)
        wallet_char2 = player.money.get(self.slug2)

        if wallet_char1 is None:
            raise AttributeError(f"{self.slug1} has no wallet")
        if wallet_char2 is None:
            logger.info(f"{self.slug2} has no wallet, setting it.")
            client.event_engine.execute_action("set_money", [self.slug2], True)
        if self.amount < 0:
            raise AttributeError(f"Value {self.amount} must be >= 0")
        if self.amount > wallet_char1:
            raise AttributeError(
                f"{self.slug1}'s wallet doesn't have {self.amount}"
            )

        _negative = -abs(self.amount)
        _positive = self.amount

        giver = [self.slug1, _negative]
        receiver = [self.slug2, _positive]
        client.event_engine.execute_action("modify_money", giver, True)
        client.event_engine.execute_action("modify_money", receiver, True)
        logger.info(f"{self.slug1} transfer {self.amount} to {self.slug2}")
