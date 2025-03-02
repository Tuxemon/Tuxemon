# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class OneOfCondition(EventCondition):
    """
    Check to see if at least 1 among multiple values in a variable
    is True.

    If the variable does not exist it will return ``False``.

    Script usage:
        .. code-block::

            is one_of <variable>[,values]

    Script parameters:
        variable: The variable to check.
        values: Value to check for (multiple values separated by ":").

    eg. "is one_of stage_of_day,afternoon:dusk:morning"

    """

    name = "one_of"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        key = condition.parameters[0]
        values = condition.parameters[1].split(":")

        if key not in player.game_variables:
            return False

        result = [
            value for value in values if player.game_variables[key] == value
        ]

        return bool(result)
