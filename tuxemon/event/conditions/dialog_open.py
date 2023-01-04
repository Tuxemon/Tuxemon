# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class DialogOpenCondition(EventCondition):
    """
    Check to see if a dialog window is open.

    Script usage:
        .. code-block::

            is dialog_open

    """

    name = "dialog_open"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a dialog window is open.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether a dialog window is open or not.
        """
        for state in session.client.active_states:
            if state.name == "DialogState":
                return True

        return False
