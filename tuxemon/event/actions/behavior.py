# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class BehaviorAction(EventAction):
    """
    Triggers behavior's action.

    Behavior is a combination of actions and conditions.

    """

    name = "behav"
    behavior: str

    def start(self) -> None:
        values = self.behavior.split(":")
        behavior = values[0]
        _action: dict[str, list[Any]] = {}
        if behavior == "talk":
            _character = values[1]
            _action["char_face"] = [_character, "player"]
        elif behavior == "door":
            _destination, _x, _y, _direction = values[2:6]
            _action["transition_teleport"] = [_destination, int(_x), int(_y)]
            _action["char_face"] = ["player", _direction]
        if _action:
            client = self.session.client.event_engine
            for _act, _params in _action.items():
                client.execute_action(_act, _params, False)
