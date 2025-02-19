# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon import formula
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class OnceCondition(EventCondition):
    """
    Checks the date saved in the variables with today's date.

    Script usage:
        .. code-block::

            is once <timeframe>,<variable>

    Script parameters:
        timeframe: nr of days the event stays "blocked" (eg. 1, 7, etc.)
        variable: Variable where the date is stored.

    """

    name = "once"

    def test(self, session: Session, condition: MapCondition) -> bool:
        timeframe = int(condition.parameters[0])
        variable = condition.parameters[1]
        player = session.player
        if variable in player.game_variables:
            today = int(player.game_variables[variable])
            if today + timeframe <= formula.today_ordinal():
                return True
            else:
                return False
        return True
