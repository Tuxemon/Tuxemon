# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class TimestampCooldownCondition(EventCondition):
    """
    Checks if a specified number of seconds has passed since the event last ran.

    This allows for more precise cooldowns than the "once per day" check.

    Script usage:
        .. code-block::

            is timestamp_cooldown <timeframe>,<variable>

    Script parameters:
        timeframe: The number of seconds the event should be on cooldown.
        variable: The game variable where the cooldown timestamp is stored.
    """

    name: ClassVar[str] = "timestamp_cooldown"
    timeframe: float
    variable: str

    def test(self, session: Session) -> bool:
        player = session.player
        current_timestamp = time.time()

        if player.game_variables.has(self.variable):
            cooldown_timestamp = float(
                player.game_variables.get(self.variable)
            )
            if current_timestamp < cooldown_timestamp:
                return False  # Event is still on cooldown.

        new_cooldown_timestamp = current_timestamp + self.timeframe
        player.game_variables.set(self.variable, new_cooldown_timestamp)
        return True
