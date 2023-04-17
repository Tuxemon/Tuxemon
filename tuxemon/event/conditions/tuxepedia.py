# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from operator import eq, ge, gt, le, lt, ne

from tuxemon.db import SeenStatus, db
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class TuxepediaCondition(EventCondition):
    """
    Check Tuxepedia's progress.

    Script usage:
        .. code-block::

            is tuxepedia <operator>,<percentage>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        percentage: Number between 0.1 and 1.0

    """

    name = "tuxepedia"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check Tuxepedia's progress.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has seen or caught a monster.

        """
        player = session.player

        # Read the parameters
        operator = condition.parameters[0]
        amount: float = 0.0
        # Tuxepedia data
        monsters = list(db.database["monster"])
        filters = []
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0:
                filters.append(results)
        tuxepedia = list(player.tuxepedia.values())
        caught = tuxepedia.count(SeenStatus.caught)
        seen = tuxepedia.count(SeenStatus.seen) + caught
        percentage = round((seen / len(filters)), 1)
        # Check number
        value = float(condition.parameters[1])
        if 0.0 <= value <= 1.0:
            amount = value
        else:
            raise ValueError(
                f"{value} must be between 0.0 and 1.0",
            )
        # Check if the condition is true
        if operator == "less_than":
            return bool(lt(percentage, amount))
        elif operator == "less_or_equal":
            return bool(le(percentage, amount))
        elif operator == "greater_than":
            return bool(gt(percentage, amount))
        elif operator == "greater_or_equal":
            return bool(ge(percentage, amount))
        elif operator == "equals":
            return bool(eq(percentage, amount))
        elif operator == "not_equals":
            return bool(ne(percentage, amount))
        else:
            raise ValueError(f"{operator} is incorrect.")
