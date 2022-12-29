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


class HasTechCondition(EventCondition):
    """
    Check to see if the player has a technique in his party.

    Script usage:
        .. code-block::

            is has_tech <technique>

    Script parameters:
        technique: Technique slug name (e.g. "bullet").

    """

    name = "has_tech"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has a technique in his party.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has a technique in his party.

        """
        player = session.player
        tech = condition.parameters[0]
        if player.has_tech(tech):
            return True
        else:
            return False
