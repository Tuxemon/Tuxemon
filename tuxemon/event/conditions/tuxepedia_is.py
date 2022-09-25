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


class TuxepediaIsCondition(EventCondition):
    """
    Check to see if the player has seen or caught a monster.

    Script usage:
        .. code-block::

            is tuxepedia_is <monster_slug>,<string>

    Script parameters:
        monster_slug: Monster slug name (e.g. "rockitten").
        string: seen / caught

    """

    name = "tuxepedia_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if the player has been seen or caught a monster.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the player has seen or caught a monster.

        """
        player = session.player

        # Read the parameters
        monster_key = condition.parameters[0]
        monster_str = condition.parameters[1]

        if monster_key in player.tuxepedia:
            if player.tuxepedia[monster_key] == monster_str:
                return True
            else:
                return False
        else:
            return False
