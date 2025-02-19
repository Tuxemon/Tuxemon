# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class WaitAction(EventAction):
    """
    Block event chain for some time.

    Script usage:
        .. code-block::

            wait <seconds>

    Script parameters:
        seconds: Time in seconds for the event engine to wait for.

    """

    name = "wait"
    seconds: float

    # TODO: use event loop time, not wall clock
    def start(self) -> None:
        self.finish_time = time.time() + self.seconds

    def update(self) -> None:
        if time.time() >= self.finish_time:
            self.stop()
