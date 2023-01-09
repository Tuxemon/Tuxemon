# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class MoneyIsCondition(EventCondition):
    """
    Check to see if the player has seen or caught a monster.

    Script usage:
        .. code-block::

            is money_is <slug>,<operator>,<value>

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        operator: One of "==", "!=", ">", ">=", "<" or "<=".
        amount: amoung of money

    """

    name = "money_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has seen or caught a monster.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has seen or caught a monster.

        """
        player = session.player

        # Read the parameters
        wallet = condition.parameters[0]
        operator = condition.parameters[1]
        amount = condition.parameters[2]

        # Check if the condition is true
        if wallet in player.money:
            if operator == "==":
                return player.money[wallet] == int(amount)
            elif operator == "!=":
                return player.money[wallet] != int(amount)
            elif operator == ">":
                return player.money[wallet] > int(amount)
            elif operator == ">=":
                return player.money[wallet] >= int(amount)
            elif operator == "<":
                return player.money[wallet] < int(amount)
            elif operator == "<=":
                return player.money[wallet] <= int(amount)
            else:
                raise ValueError(f"invalid operation type {operator}")
        else:
            return False
