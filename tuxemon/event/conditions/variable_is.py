# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import number_or_variable

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
            raise ValueError(f"invalid operation type {operation}")
