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
class PartySizeCondition(EventCondition):
    """
    Check the character's party size.

    Script usage:
        .. code-block::

            is party_size <character>,<operator>,<value>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value: The value to compare the party size with.

    """

    name = "party_size"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, _operator, _value = condition.parameters[:3]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        return compare(_operator, len(character.monsters), int(_value))
