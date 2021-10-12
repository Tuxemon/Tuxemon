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
from tuxemon.tools import number_or_variable
from tuxemon.session import Session
from tuxemon.event import MapCondition

logger = logging.getLogger(__name__)


class VariableIsCondition(EventCondition):
    """
    Check an operation over a variable.

    Script usage:
        .. code-block::

            is variable_is <value1>,<operation>,<value2>

    Script parameters:
        value1: Either a variable or a number.
        operation: One of "==", "!=", ">", ">=", "<" or "<=".
        value2: Either a variable or a number.

    """

    name = "variable_is"

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
            logger.error(f"invalid operation type {operation}")
            raise ValueError
