# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


class HasBagCondition(EventCondition):
    """
    Check to see how many items are in the character's bag.

    Script usage:
        .. code-block::

            is has_bag <character>,<operator>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the bag with.

    """

    name = "has_bag"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, check, _number = condition.parameters[:3]
        number = int(_number)
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        sum_total = []
        for itm in character.items:
            if itm.visible:
                sum_total.append(itm.quantity)
        bag_size = sum(sum_total)
        return compare(check, bag_size, number)
