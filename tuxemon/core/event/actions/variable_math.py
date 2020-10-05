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

from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.tools import number_or_variable

logger = logging.getLogger(__name__)


class VariableMathAction(EventAction):
    """ Preforms a mathematical operation on the key in the player.game_variables dictionary.

    Valid Parameters: variable_name, operation, value
    """
    name = "variable_math"
    valid_parameters = [
        (str, "var"),
        (str, "operation"),
        (str, "value")
    ]

    def start(self):
        player = self.session.player

        # Read the parameters
        var = self.parameters.var
        operand1 = number_or_variable(self.session, var)
        operation = self.parameters.operation
        operand2 = number_or_variable(self.session, self.parameters.value)

        # Preform the operation on the variable
        if operation == "+":
            player.game_variables[var] = operand1 + operand2
        elif operation == "-":
            player.game_variables[var] = operand1 - operand2
        elif operation == "*":
            player.game_variables[var] = operand1 * operand2
        elif operation == "/":
            player.game_variables[var] = operand1 / operand2
        else:
            logger.error("invalid operation type {}".format(operation))
            raise ValueError
