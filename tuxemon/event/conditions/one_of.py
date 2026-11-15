# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class OneOfCondition(EventCondition):
    """
    Check to see if at least 1 among multiple values in a variable
    is True.

    If the variable does not exist it will return ``False``.

    Script usage:
        .. code-block::

            is one_of <variable>[,values]

    Script parameters:
        variable: The variable to check.
        values: Value to check for (multiple values separated by ":").

    eg. "is one_of name_variable,option1:option2:option3"
    """

    name: ClassVar[str] = "one_of"
    variable: str
    values: str

    def test(self, session: Session) -> bool:
        player = session.player
        values = self.values.split(":")

        if not player.game_variables.has(self.variable):
            return False

        result = [
            value
            for value in values
            if player.game_variables.get(self.variable) == value
        ]

        return bool(result)
