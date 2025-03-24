# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
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
        slug: Either "player" or character slug name (e.g. "npc_maple").
        amount: Amount of money to add/remove (-/+)
        variable: Name of the variable where to store the amount.

    eg. "modify_money player,-50"
    eg. "modify_money player,,name_variable"

    """

    name = "modify_money"
    character: str
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
                    _wallet = money_manager.get_money()
                    amount = int(_wallet * _value)
                else:
                    raise ValueError("It must be float or int")
            else:
                amount = 0
        else:
            amount = self.amount

        money_manager.add_money(amount)
        logger.info(f"{character.name}'s money changed by {amount}")
