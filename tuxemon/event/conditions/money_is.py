# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
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

    name = "money_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        character_name, operator, _amount = condition.parameters[:3]
        character = get_npc(session, character_name)
        if character is None:
            logger.error(f"Character '{character_name}' not found")
            return False

        if not _amount.isdigit():
            amount = 0
            if _amount in player.game_variables:
                amount = int(player.game_variables.get(_amount, 0))
        else:
            amount = int(_amount)

        money_manager = character.money_controller.money_manager
        money_amount = money_manager.get_money()
        return compare(operator, money_amount, amount)
