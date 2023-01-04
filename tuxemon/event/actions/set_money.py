# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetMoneyAction(EventAction):
    """
    Set the key and value in the money dictionary.

    Script usage:
        .. code-block::

            set_money <slug>,<amount>

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        amount: amoung of money

    """

    name = "set_money"
    wallet: str
    amount: int

    def start(self) -> None:
        # Append the money with a key
        self.session.player.money[str(self.wallet)] = self.amount
