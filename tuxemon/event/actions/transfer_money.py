# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class TransferMoneyAction(EventAction):
    """
    Transfer money between entities.

    Script usage:
        .. code-block::

            transfer_money <slug1>,<amount>,<slug2>

    Script parameters:
        slug1: Either "player" or character slug name (e.g. "npc_maple").
        amount: amount of money.
        slug2: Either "player" or character slug name (e.g. "npc_maple").

    eg: player,100,mom (player transfer 100 to mom)
    """

    name = "transfer_money"
    slug1: str
    amount: int
    slug2: str

    def start(self) -> None:
        character1 = get_npc(self.session, self.slug1)
        character2 = get_npc(self.session, self.slug2)

        if not character1 or not character2:
            _char = self.slug1 if not character1 else self.slug2
            logger.error(f"Character not found in map: {_char}")
            return

        money_manager = character1.money_controller.money_manager

        if self.amount < 0:
            raise AttributeError(f"Value {self.amount} must be >= 0")
        if self.amount > money_manager.get_money():
            raise AttributeError(
                f"{self.slug1}'s wallet doesn't have {self.amount}"
            )

        character1.money_controller.transfer_money_to(self.amount, character2)
        logger.info(
            f"{character1.name} transfer {self.amount} to {character2.name}"
        )
