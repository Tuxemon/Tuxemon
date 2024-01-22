# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import SeenStatus, db
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


class TuxepediaCondition(EventCondition):
    """
    Check Tuxepedia's progress.

    Script usage:
        .. code-block::

            is tuxepedia <operator>,<percentage>[,total]

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        percentage: Number between 0.1 and 1.0
        total: Total, by default the tot number of tuxemon.

    """

    name = "tuxepedia"

    def test(self, session: Session, condition: MapCondition) -> bool:
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
        # Total monsters
        total = len(filters)
        if len(condition.parameters) == 3:
            total = int(condition.parameters[2])
        # Tuxepedia operation
        tuxepedia = list(player.tuxepedia.values())
        caught = tuxepedia.count(SeenStatus.caught)
        seen = tuxepedia.count(SeenStatus.seen) + caught
        percentage = round((seen / total), 1)
        # Check number
        value = float(condition.parameters[1])
        if 0.0 <= value <= 1.0:
            amount = value
        else:
            raise ValueError(
                f"{value} must be between 0.0 and 1.0",
            )
        return compare(operator, percentage, amount)
