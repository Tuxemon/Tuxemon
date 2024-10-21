# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import MapCondition, get_npc
from tuxemon.event.conditions.common import CommonCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@final
@dataclass
class CheckPartyParameterCondition(EventCondition):
    """
    Check the given attribute of the party.

    Script usage:
        .. code-block::

            check_party_parameter <character>,<attribute>,<value>,<operator>,<times>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        attribute: Name of the monster attribute to check (e.g. level).
        value: Value to check (related to the attribute) (e.g. 5 - level).
        operator: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        times: Value to check with operator (how many times in the party?).

    eg. "check_party_parameter player,level,5,equals,1"
    translated: "is there 1 monster in the party at level 5? True/False"

    """

    name = "check_party_parameter"

    def test(self, session: Session, condition: MapCondition) -> bool:
        (
            _character,
            _attribute,
            _value,
            _operator,
            _times,
        ) = condition.parameters[:5]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        if not character.monsters:
            logger.warning(f"{character.name} has no monsters")
            return False
        party = len(character.monsters)
        times = party if int(_times) > party else int(_times)

        count = sum(
            1
            for monster in character.monsters
            if CommonCondition.check_parameter(monster, _attribute, _value)
        )
        return compare(_operator, count, times)
