# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from operator import eq, ge, gt, le, lt, ne

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class HasBoxCondition(EventCondition):
    """
    Check to see how many monsters are in the box.

    Script usage:
        .. code-block::

            is has_box <box>,<operator>,<value>

    Script parameters:
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party with.
        box: The box name.

    """

    name = "has_box"

    def test(self, session: Session, condition: MapCondition) -> bool:
        box_name = str(condition.parameters[0])
        check = str(condition.parameters[1])
        number = int(condition.parameters[2])
        player = session.player
        if box_name not in player.monster_boxes.keys():
            raise ValueError(f"{box_name} doesn't exist.")
        party_size = len(player.monster_boxes[box_name])
        if check == "less_than":
            return bool(lt(party_size, number))
        elif check == "less_or_equal":
            return bool(le(party_size, number))
        elif check == "greater_than":
            return bool(gt(party_size, number))
        elif check == "greater_or_equal":
            return bool(ge(party_size, number))
        elif check == "equals":
            return bool(eq(party_size, number))
        elif check == "not_equals":
            return bool(ne(party_size, number))
        else:
            raise ValueError(f"{check} is incorrect.")
