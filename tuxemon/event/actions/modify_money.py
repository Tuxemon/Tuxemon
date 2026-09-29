# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

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
                    wallet = money_manager.get_money()
                    amount = int(wallet * raw_value)

                else:
                    raise ValueError(
                        f"Variable '{self.variable}' must be int or float, got {type(raw_value).__name__}"
                    )
            else:
                amount = 0
        else:
            amount = self.amount

        current_money = money_manager.get_money()
        if amount < 0 and current_money + amount < 0:
            raise ValueError(
                f"Cannot remove {abs(amount)} money: only {current_money} available"
            )

        money_manager.add_money(amount)

        logger.debug(
            f"{character.name}'s money changed by {amount}. "
            f"New balance: {money_manager.get_money()}"
        )
