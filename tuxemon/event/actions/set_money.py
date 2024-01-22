# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMoneyAction(EventAction):
    """
    Set an amount of money for a specific slug.

    Script usage:
        .. code-block::

            set_money <slug>,<amount>

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        amount: Amount of money (>= 0) (default 0)

    """

    name = "set_money"
    wallet: str
    amount: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        wallet = self.wallet
        amount = 0 if self.amount is None else self.amount
        if amount < 0:
            logger.error(f"{amount} must be >= 0")
            return
        else:
            player.money[wallet] = amount
            logger.info(f"{wallet}'s have {amount}")
