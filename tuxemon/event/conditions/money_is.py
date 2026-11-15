# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class MoneyIsCondition(EventCondition):
    """
    Check to see if the character has a certain amount of money (pocket).

    Script usage:
        .. code-block::

            is money_is <character>,<operator>,<amount>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        amount: Amount of money or value stored in variable

    eg. "is money_is player,equals,50"
    eg. "is money_is player,equals,name_variable" (name_variable:75)
    """

    name: ClassVar[str] = "money_is"
    character: str
    operator: str
    amount: str | int

    def test(self, session: Session) -> bool:
        player = session.player
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"Character '{self.character}' not found")
            return False

        if isinstance(self.amount, str):
            amount = 0
            if player.game_variables.has(self.amount):
                amount = int(player.game_variables.get(self.amount, 0))
        else:
            amount = self.amount

        money_manager = character.money_controller.money_manager
        money_amount = money_manager.get_money()
        return compare(self.operator, money_amount, amount)
