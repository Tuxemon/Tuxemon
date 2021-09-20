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
import logging

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.event import MapCondition

logger = logging.getLogger(__name__)


class PartySizeCondition(EventCondition):
    """
    Check the party size.

    Script usage:
        .. code-block::

            is party_size <operator> <value>

    Script parameters:
        operator: One of "equals", "less_than" or "greater_than".
        value: The value to compare the party size with.

    """

    name = "party_size"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check the party size.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Result of the comparison between the party size and the chosen
            value.

        """
        check = str(condition.parameters[0])
        number = int(condition.parameters[1])
        party_size = len(session.player.monsters)

        # Check to see if the player's party size equals this number.
        if check == "equals":
            logger.debug("Equal check")
            return party_size == number

        # Check to see if the player's party size is LESS than this number.
        elif check == "less_than":
            return party_size < number

        # Check to see if the player's part size is GREATER than this number.
        elif check == "greater_than":
            return party_size > number

        else:
            raise Exception("Party size check parameters are incorrect.")
