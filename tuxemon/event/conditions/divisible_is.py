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

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import number_or_variable

logger = logging.getLogger(__name__)


class DivisibleIsCondition(EventCondition):
    """
    Check an operation over a variable.

    Script usage:
        .. code-block::

            is divisible_is <value>,<operation>

    Script parameters:
        value: Either a variable or a number.
        operation: One of "2", "3", "5", "7", etc.

    """

    name = "divisible_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check an operation over a variable.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Result of the operation over the variable.

        """

        # Read the parameters
        value = number_or_variable(session, condition.parameters[0])
        divisor = condition.parameters[1]

        # Check if the condition is true
        if (value % divisor) == 0:
            return True
        else:
            return False
