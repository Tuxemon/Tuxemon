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

logger = logging.getLogger(__name__)


@final
@dataclass
class CheckCharParameterCondition(EventCondition):
    """
    Check the parameter's value of the character against a given value.

    Script usage:
        .. code-block::

            check_char_parameter <character>,<parameter>,<value>

    Script parameters:
        character: Either "player" or npc slug name (eg. "npc_maple").
        parameter: Name of the parameter to check (eg. "name", "steps", etc.).
        value: Given value to check.

    eg. "player,name,alpha" -> is the player named alpha? true/false

    """

    name = "check_char_parameter"

    def test(self, session: Session, condition: MapCondition) -> bool:
        _character, _parameter, _value = condition.parameters[:3]
        character = get_npc(session, _character)
        if character is None:
            logger.error(f"{_character} not found")
            return False
        return CommonCondition.check_parameter(character, _parameter, _value)
