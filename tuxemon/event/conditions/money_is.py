# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from operator import eq, ge, gt, le, lt, ne

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class MoneyIsCondition(EventCondition):
    """
    Check to see if the player has a certain amount of money (pocket).

    Script usage:
        .. code-block::

            is money_is <slug>,<operator>,<value>

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        amount: Amount of money

    """

    name = "money_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has a certain amount of money (pocket).

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has a certain amount of money.

        """
        player = session.player

        # Read the parameters
        wallet = condition.parameters[0]
        operator = condition.parameters[1]
        amount = condition.parameters[2]

        # Check if the condition is true
        if wallet in player.money:
            if operator == "less_than":
                return bool(lt(player.money[wallet], int(amount)))
            elif operator == "less_or_equal":
                return bool(le(player.money[wallet], int(amount)))
            elif operator == "greater_than":
                return bool(gt(player.money[wallet], int(amount)))
            elif operator == "greater_or_equal":
                return bool(ge(player.money[wallet], int(amount)))
            elif operator == "equals":
                return bool(eq(player.money[wallet], int(amount)))
            elif operator == "not_equals":
                return bool(ne(player.money[wallet], int(amount)))
            else:
                logger.error(f"{operator} is incorrect.")
                raise ValueError()
        else:
            return False
