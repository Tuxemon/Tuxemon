# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare


class HasBagCondition(EventCondition):
    """
    Check to see how many items are in the bag.

    Script usage:
        .. code-block::

            is has_bag <operator>,<value>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the bag with.

    """

    name = "has_bag"

    def test(self, session: Session, condition: MapCondition) -> bool:
        check = str(condition.parameters[0])
        number = int(condition.parameters[1])
        player = session.player
        sum_total = []
        for itm in player.items:
            if itm.visible:
                sum_total.append(itm.quantity)
        bag_size = sum(sum_total)
        return compare(check, bag_size, number)
