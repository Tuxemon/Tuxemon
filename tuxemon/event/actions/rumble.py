# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.rumble.tools import RumbleParams
from tuxemon.session import Session


@final
@dataclass
class RumbleAction(EventAction):
    """
    Rumble available controllers with rumble support.

    Script usage:
        .. code-block::

            rumble <duration>,<power>[,period][,delay][,attack_length]
                [,attack_level][,fade_length][,fade_level][,direction]

    Script parameters:
        duration: Time in seconds to rumble for.
        power: Percentage of power to rumble (0 to 100).
        period: Time period between vibrations in milliseconds.
            Default 25.
        delay: Time in seconds before the rumble starts.
            Default 0.
        attack_length: Time in milliseconds for the rumble to ramp up.
            Default 256.
        attack_level: Initial intensity level during ramp-up.
            Default 0.
        fade_length: Time in milliseconds for the rumble to fade out.
            Default 256.
        fade_level: Final intensity level during ramp-down.
            Default 0.
        direction: Direction of the rumble effect, for spatial control.
            Default 16384.
    """

    name = "rumble"
    duration: float
    power: int
    period: float = 25
    delay: float = 0
    attack_length: float = 256
    attack_level: float = 0
    fade_length: float = 256
    fade_level: float = 0
    direction: float = 16384

    def start(self, session: Session) -> None:
        max_power = 24576  # Maximum rumble intensity
        magnitude = int((self.power * 0.01) * max_power)

        params = RumbleParams(
            target=-1,
            length=self.duration,
            magnitude=magnitude,
            period=self.period,
            delay=self.delay,
            attack_length=self.attack_length,
            attack_level=self.attack_level,
            fade_length=self.fade_length,
            fade_level=self.fade_level,
            direction=self.direction,
        )
        session.client.rumble.rumble(params)
