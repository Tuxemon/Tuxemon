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

import logging

from tuxemon.core.event.eventcondition import EventCondition

logger = logging.getLogger(__name__)


class PartySizeCondition(EventCondition):
    """ Checks to see where an NPC is facing
    """
    name = "party_size"

    def test(self, session,  condition):
        """Perform various checks about the player's party size. With this condition you can see if
        the player's party is less than, greater than, or equal to then number you specify.

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
            for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: check,party_size

        The "check" parameter can be one of the following: "equals", "less_than", or "greater_than".

        **Examples:**

        >>> condition.__dict__
        {
            "type": "party_size",
            "parameters": [
                "less_than",
                "2"
            ],
            "width": 1,
            "height": 1,
            "operator": "is",
            "x": 6,
            "y": 9,
            ...
        }

        """
        check = str(condition.parameters[0])
        number = int(condition.parameters[1])
        party_size = len(session.player.monsters)

        # Check to see if the player's party size equals this number.
        if check == "equals":
            logger.debug("Equal check")
            if party_size == number:
                return True
            else:
                return False

        # Check to see if the player's party size is LESS than this number.
        elif check == "less_than":
            if party_size < number:
                return True
            else:
                return False

        # Check to see if the player's part size is GREATER than this number.
        elif check == "greater_than":
            if party_size > number:
                return True
            else:
                return False

        else:
            raise Exception("Party size check parameters are incorrect.")

        return False
