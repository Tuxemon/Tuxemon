# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.time_handler import today_ordinal


@dataclass
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

        if variable not in player.game_variables:
            player.game_variables[variable] = today_ordinal()
            return True

        last_occurrence_day = int(player.game_variables[variable])
        current_day = today_ordinal()

        if current_day - last_occurrence_day > timeframe:
            player.game_variables[variable] = current_day
            return True

        return False
