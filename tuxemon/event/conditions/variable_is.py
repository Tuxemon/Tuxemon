# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare, number_or_variable


@dataclass
class VariableIsCondition(EventCondition):
    """
    Check an operation over a variable.

    Script usage:
        .. code-block::

            is variable_is <value1>,<operation>,<value2>

    Script parameters:
        value1: Either a variable or a number.
        operation: Numeric comparison operator. Accepted values are "less_than",
            "less_or_equal", "greater_than", "greater_or_equal", "equals"
            and "not_equals".
        value2: Either a variable or a number.

    """

    name = "variable_is"

    def test(self, session: Session, condition: MapCondition) -> bool:
        # Read the parameters
        operand1 = number_or_variable(session, condition.parameters[0])
        operation = condition.parameters[1]
        operand2 = number_or_variable(session, condition.parameters[2])
        return compare(operation, operand1, operand2)
