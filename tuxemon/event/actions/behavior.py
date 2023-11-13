# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class BehaviorAction(EventAction):
    """
    Triggers behaviors action.

    """

    name = "behav"
    behavior: str
    value1: Optional[str] = None
    value2: Optional[str] = None
    value3: Optional[str] = None

    def start(self) -> None:
        _e = self.session.client.event_engine
        if self.behavior == "talk":
            _e.execute_action(
                "npc_face",
                [
                    self.value1,
                    "player",
                ],
                True,
            )
        elif self.behavior == "door":
            _e.execute_action(
                "player_face",
                [
                    self.value2,
                ],
                True,
            )
