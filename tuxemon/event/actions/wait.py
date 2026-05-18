# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class WaitAction(EventAction):
    """
    Block the event chain for a given duration.

    Script usage:
        .. code-block::

            wait <seconds>

    Script parameters:
        seconds: Duration in seconds for the event engine to wait.
                The wait is measured using accumulated delta time (dt)
                from the game loop, not wall clock time.
    """

    name = "wait"
    seconds: float
    elapsed: float = 0.0

    def start(self, session: Session) -> None:
        self.elapsed = 0.0

    def update(self, session: Session, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.seconds:
            self.stop()
