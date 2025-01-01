# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const import intentions
from tuxemon.session import Session


class ButtonPressedCondition(EventCondition):
    """
    Check to see if a particular key was pressed.

    Currently only "K_RETURN" is supported.

    Script usage:
        .. code-block::

            is button_pressed <button>

    Script parameters:
        button: A button/intention key (E.g. "K_RETURN").

    """

    name = "button_pressed"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a particular key was pressed.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the key was pressed or not.

        """
        button = str(condition.parameters[0])

        # TODO: workaround for old maps.  eventually need to decide on a scheme
        # and fix existing scripts
        if button == "K_RETURN":
            button_id = intentions.INTERACT
        else:
            raise ValueError(f"Cannot support key type: {button}")

        # Loop through each event
        for event in session.client.key_events:
            if event.pressed and event.button == button_id:
                return True

        return False
