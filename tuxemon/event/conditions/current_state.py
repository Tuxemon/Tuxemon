# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class CurrentStateCondition(EventCondition):
    """
    Check to see if one or multiple state/states has/have
    been started or not.

    Script usage:
        .. code-block::

            is current_state <state>

    Script parameters:
        states: Either "CombatState", "DialogState", etc

    eg: "is current_state CombatState"
    eg: "is current_state CombatState:DialogState"
    """

    name: ClassVar[str] = "current_state"
    states: str

    def test(self, session: Session) -> bool:
        current_state = session.client.current_state
        assert current_state
        states = self.states.split(":")
        return current_state.name in states
