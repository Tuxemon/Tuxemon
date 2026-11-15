# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import re

from pygame.joystick import Joystick, JoystickType, get_count, init

logger = logging.getLogger(__name__)


class JoystickDetector:
    """
    Detects and filters physical joysticks using a blacklist.
    """

    def __init__(self) -> None:
        self.blacklist = [
            re.compile(r"Microsoft.*Transceiver.*"),
            re.compile(r".*Synaptics.*", re.I),
            re.compile(r"Wacom*.", re.I),
        ]

    def detect(self) -> list[JoystickType]:
        init()
        joysticks: list[JoystickType] = []

        for i in range(get_count()):
            try:
                js = Joystick(i)
                name = js.get_name()

                if any(p.match(name) for p in self.blacklist):
                    logger.info(f"Ignoring blacklisted joystick: {name}")
                    continue

                logger.info(f"Detected joystick: {name}")
                joysticks.append(js)

            except Exception as e:
                logger.warning(f"Failed to initialize joystick {i}: {e}")

        return joysticks
