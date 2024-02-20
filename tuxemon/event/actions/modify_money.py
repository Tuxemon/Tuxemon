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
class ModifyMoneyAction(EventAction):
    """
    Add or remove an amount of money for a wallet (slug).

    Script usage:
        .. code-block::

            modify_money <slug>,[amount][,variable]

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        amount: Amount of money to add/remove (-/+)
        variable: Name of the variable where to store the amount.

    eg. "modify_money player,-50"
    eg. "modify_money player,,name_variable"

    """

    name = "modify_money"
    wallet: str
    amount: Optional[int] = None
    variable: Optional[str] = None

    def start(self) -> None:
        client = self.session.client
        player = self.session.player
        wallet = self.wallet
        if self.amount is None:
            if self.variable:
                _amount = player.game_variables.get(self.variable, 0)
                if isinstance(_amount, int):
                    amount = int(_amount)
                elif isinstance(_amount, float):
                    _value = float(_amount)
                    _wallet = player.money.get(wallet, 0)
                    amount = int(_wallet * _value)
                else:
                    raise ValueError("It must be float or int")
            else:
                amount = 0
        else:
            amount = self.amount
        if wallet not in player.money:
            logger.info(f"{wallet} has no wallet, setting it.")
            client.event_engine.execute_action("set_money", [wallet], True)

        if amount < 0 and abs(amount) > player.money[wallet]:
            raise AttributeError(f"{wallet}'s doesn't have {abs(amount)}")
        else:
            player.money[wallet] += amount
            logger.info(f"{wallet}'s money changed by {amount}")
