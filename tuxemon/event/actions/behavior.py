# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class BehaviorAction(EventAction):
    """
    Triggers behavior's action.

    Behavior is a combination of 1 action with 1 or more conditions.

    """

    name = "behav"
    behavior: str
    value1: Optional[str] = None
    value2: Optional[str] = None
    value3: Optional[str] = None

    def start(self) -> None:
        _execute = False
        _action = ""
        _params = []
        if self.behavior == "talk":
            _execute = True
            _action = "npc_face"
            _params = [self.value1, "player"]
        elif self.behavior == "door":
            _execute = True
            _action = "player_face"
            _params = [self.value2]
        if _execute:
            client = self.session.client.event_engine
            client.execute_action(_action, _params, True)
