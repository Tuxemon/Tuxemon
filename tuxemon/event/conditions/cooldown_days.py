# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.db import SpatialCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.time_handler import today_ordinal


@dataclass
class CooldownDaysCondition(EventCondition):
    """
    Checks if a specified number of days has passed since the event last ran.

    Script usage:
        .. code-block::

            is cooldown_days <timeframe>,<variable>

    Script parameters:
        timeframe: The number of days the event should be on cooldown.
        variable: The game variable where the cooldown date is stored.
    """

    name = "cooldown_days"

    def test(self, session: Session, condition: SpatialCondition) -> bool:
        timeframe = int(condition.parameters[0])
        variable = condition.parameters[1]
        player = session.player

        if player.game_variables.has(variable):
            cooldown_day = int(player.game_variables.get(variable))
            if today_ordinal() < cooldown_day:
                return False  # Event is still on cooldown.

        new_cooldown_day = today_ordinal() + timeframe
        player.game_variables.set(variable, new_cooldown_day)
        return True
