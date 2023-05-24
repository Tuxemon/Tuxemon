# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from operator import eq, ge, gt, le, lt, ne

from tuxemon.db import ItemCategory
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


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
            # excludes the phone + apps
            if itm.category != ItemCategory.phone:
                sum_total.append(itm.quantity)
        bag_size = sum(sum_total)
        if check == "less_than":
            return bool(lt(bag_size, number))
        elif check == "less_or_equal":
            return bool(le(bag_size, number))
        elif check == "greater_than":
            return bool(gt(bag_size, number))
        elif check == "greater_or_equal":
            return bool(ge(bag_size, number))
        elif check == "equals":
            return bool(eq(bag_size, number))
        elif check == "not_equals":
            return bool(ne(bag_size, number))
        else:
            logger.error(f"{check} is incorrect.")
            raise ValueError()
