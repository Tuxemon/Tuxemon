# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
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
        state: Either "CombatState", "DialogState", etc

    eg: "is current_state CombatState"
    eg: "is current_state CombatState:DialogState"

    """

    name = "current_state"

    def test(self, session: Session, condition: MapCondition) -> bool:
        current_state = session.client.current_state
        assert current_state
        states = condition.parameters[0].split(":")
        return current_state.name in states
