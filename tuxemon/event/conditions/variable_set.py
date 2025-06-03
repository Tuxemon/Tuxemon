# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class VariableSetCondition(EventCondition):
    """
    Checks if one or more player game variables exist and optionally match
    specified values.

    If a variable does not exist, the condition returns `False`.

    Script usage:
        .. code-block::

            is variable_set <variable>[:value],[<variable>[:value] ...]

    Script parameters:
        variable: The variable to check.
        value: Optional value to check against. If omitted, the condition
            only checks for the variable's existence.

    The condition returns `True` if all specified variables exist and
    match their given values (if provided). Otherwise, it returns `False`.
    """

    name = "variable_set"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player

        return all(
            key in player.game_variables
            and (not value or player.game_variables[key] == value)
            for part in condition.parameters
            for key, _, value in [part.partition(":")]
        )
