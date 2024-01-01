# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


class HasBoxCondition(EventCondition):
    """
    Check to see how many monsters are in the character's box.

    Script usage:
        .. code-block::

            is has_box <character>,<box>,<operator>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party with.
        box: The box name.

    """

    name = "has_box"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, box_name, check, _number = condition.parameters[:4]
        number = int(_number)
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        if box_name not in character.monster_boxes.keys():
            raise ValueError(f"{box_name} doesn't exist.")
        party_size = len(character.monster_boxes[box_name])
        return compare(check, party_size, number)
