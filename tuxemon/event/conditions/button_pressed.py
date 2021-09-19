#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import annotations
from tuxemon.event.eventcondition import EventCondition
from tuxemon.platform.const import intentions
from tuxemon.session import Session
from tuxemon.event import MapCondition


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
