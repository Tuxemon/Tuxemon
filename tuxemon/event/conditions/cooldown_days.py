# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


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

    name: ClassVar[str] = "cooldown_days"
    timeframe: int
    variable: str

    def test(self, session: Session) -> bool:
        player = session.player

        if player.game_variables.has(self.variable):
            cooldown_day = int(player.game_variables.get(self.variable))
            if session.time.get_ordinal() < cooldown_day:
                return False  # Event is still on cooldown.

        new_cooldown_day = session.time.get_ordinal() + self.timeframe
        player.game_variables.set(self.variable, new_cooldown_day)
        return True
