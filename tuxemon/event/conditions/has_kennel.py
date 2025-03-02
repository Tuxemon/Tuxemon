# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class HasKennelCondition(EventCondition):
    """
    Check to see how many monsters are in the character's kennel.

    Script usage:
        .. code-block::

            is has_kennel <character>,<kennel>,<operator>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        kennel: The kennel name.
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party with.

    """

    name = "has_kennel"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, kennel_name, check, _number = condition.parameters[:4]
        number = int(_number)
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        if not character.monster_boxes.has_box(kennel_name, "monster"):
            raise ValueError(f"{kennel_name} doesn't exist.")
        party_size = character.monster_boxes.get_box_size(
            kennel_name, "monster"
        )
        return compare(check, party_size, number)
