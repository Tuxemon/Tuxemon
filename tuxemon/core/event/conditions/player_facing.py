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

from tuxemon.core.event.eventcondition import EventCondition


class PlayerFacingCondition(EventCondition):
    """ Checks to see where an NPC is facing
    """
    name = "player_facing"

    def test(self, session,  condition):
        """Checks to see where the player is facing

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: direction ("up", "down", "left" or "right")

        **Examples:**

        >>> condition.__dict__
        {
            "type": "player_facing",
            "parameters": [
                "up"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """
        player = session.player
        facing = condition.parameters[0]

        if player.facing == facing:
            return True
        else:
            return False
