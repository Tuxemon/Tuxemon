# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.tools import number_or_variable

logger = logging.getLogger(__name__)


@final
@dataclass
class VariableMathAction(EventAction):
    """
    Perform a mathematical operation on the player.game_variables dictionary.

    Optionally accepts a fourth parameter to store the result, otherwise it
    is stored in ``var1``.

    Script usage:
        .. code-block::

            variable_math <var1>,<operation>,<var2>,<result>
            variable_math <var1>,<operation>,<var2>

    Script parameters:
        var1: First operand.
        operation: Operator symbol.
        var2: Second operand.
        result: Variable where to store the result. If missing, it will be
            ``var1``.

    """

    name = "variable_math"
    var1: str
    operation: str
    var2: str
    result: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player

        # Read the parameters
        var = self.var1
        result = self.result
        if result is None:
            result = var
        operand1 = number_or_variable(self.session, var)
        operation = self.operation
        operand2 = number_or_variable(self.session, self.var2)

        # Perform the operation on the variable
        if operation == "+":
            player.game_variables[result] = operand1 + operand2
        elif operation == "-":
            player.game_variables[result] = operand1 - operand2
        elif operation == "*":
            player.game_variables[result] = operand1 * operand2
        elif operation == "/":
            player.game_variables[result] = operand1 / operand2
        elif operation == "=":
            player.game_variables[result] = operand2
        else:
            logger.error(f"invalid operation type {operation}")
            raise ValueError()
