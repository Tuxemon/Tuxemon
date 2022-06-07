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
