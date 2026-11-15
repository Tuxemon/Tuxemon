# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.conditions.common import CommonCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


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

    name: ClassVar[str] = "check_char_parameter"
    character: str
    param: str
    value: str

    def test(self, session: Session) -> bool:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return False
        return CommonCondition.check_parameter(
            character, self.param, self.value
        )
