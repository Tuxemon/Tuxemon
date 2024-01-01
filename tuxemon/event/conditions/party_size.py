# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


class PartySizeCondition(EventCondition):
    """
    Check the party size.

    Script usage:
        .. code-block::

            is party_size <operator>,<value>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party size with.

    """

    name = "party_size"

    def test(self, session: Session, condition: MapCondition) -> bool:
        operator, value = condition.parameters[:2]
        party_size = len(session.player.monsters)
        return compare(operator, party_size, int(value))
