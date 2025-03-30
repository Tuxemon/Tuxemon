# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class RumbleAction(EventAction):
    """
    Rumble available controllers with rumble support.

    Script usage:
        .. code-block::

            rumble <duration>,<power>

    Script parameters:
        duration: Time in seconds to rumble for.
        power: Percentage of power to rumble.

    """

    name = "rumble"
    duration: float
    power: int

    def start(self) -> None:
        duration = float(self.duration)
        power = int(self.power)

        min_power = 0
        max_power = 24576

        if power < 0:
            power = 0
        elif power > 100:
            power = 100

        magnitude = int((power * 0.01) * max_power)
        self.session.client.rumble.rumble(
            -1,
            length=duration,
            magnitude=magnitude,
        )
