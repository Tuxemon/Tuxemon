# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class CombatStartedCondition(EventCondition):
    """
    Check to see if combat has been started or not.

    Script usage:
        .. code-block::

            is combat_started

    """

    name = "combat_started"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if combat has been started or not.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether a combat has started or not.

        """
        current_state = session.client.current_state
        assert current_state
        return current_state.name == "CombatState"
