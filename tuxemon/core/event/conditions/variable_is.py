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
from tuxemon.core.tools import number_or_variable

logger = logging.getLogger(__name__)


class VariableIsCondition(EventCondition):
    """ Checks to see if a player game variable has been set. This will look for a particular
    key in the player.game_variables dictionary and see if it exists. If it exists, it will
    return true.
    """
    name = "variable_is"

    def test(self, session,  condition):
        """ Checks to see if a player game variable meets a given condition. This will look
        for a particular key in the player.game_variables dictionary and see if it exists.
        If it exists, it will return true if the variable is greater than the value.

        :param session: The session object
        :param condition: A dictionary of condition details. See :py:func:`core.map.Map.loadevents`
        for the format of the dictionary.

        :type session: tuxemon.core.session.Session
        :type condition: Dictionary

        :rtype: Boolean
        :returns: True or False

        Valid Parameters: variable_name, operation, value
        """
        player = session.player

        # Read the parameters
        operand1 = number_or_variable(session, condition.parameters[0])
        operation = condition.parameters[1]
        operand2 = number_or_variable(session, condition.parameters[2])

        # Check if the condition is true
        if operation == "==":
            return operand1 == operand2
        elif operation == "!=":
            return operand1 != operand2
        elif operation == ">":
            return operand1 > operand2
        elif operation == ">=":
            return operand1 >= operand2
        elif operation == "<":
            return operand1 < operand2
        elif operation == "<=":
            return operand1 <= operand2
        else:
            logger.error("invalid operation type {}".format(operation))
            raise ValueError
