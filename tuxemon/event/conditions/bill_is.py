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
class BillIsCondition(EventCondition):
    """
    Check to see if a bill exists and has a certain amount.

    Script usage:
        .. code-block::

            is bill_is <character>,<operator>,<bill_slug>,<amount>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        bill_slug: The slug of the bill
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        amount: Amount of money or value stored in variable

    eg. "is bill_is player,bill_slug,equals,50"
    eg. "is bill_is player,bill_slug,equals,name_variable" (name_variable:75)

    """

    name = "bill_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        character_name, _bill, operator, _amount = condition.parameters[:4]
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
        bill_amount = money_manager.get_bill(_bill).amount
        if bill_amount == 0:
            return False
        else:
            return compare(operator, bill_amount, amount)
