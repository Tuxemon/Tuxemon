# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class RumblePatternAction(EventAction):
    """
    Play a named rumble pattern on available controllers.

    Script usage:
        .. code-block::

            rumble_pattern <pattern_name>[,target]

    Script parameters:
        pattern_name: Name of the pattern ('pulse', 'heartbeat', 'explosion').
        target: Optional device index (-1 for all). Default -1.
    """

    name = "rumble_pattern"
    pattern_name: str
    target: int = -1

    def start(self, session: Session) -> None:
        session.client.rumble_manager.play_pattern(
            self.target, self.pattern_name
        )
