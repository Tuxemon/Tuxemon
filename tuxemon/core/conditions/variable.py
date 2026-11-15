# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class VariableCondition(CoreCondition):
    """
    Checks a game variable against an expected value.

    **Parameters**
    - ``var_name``: The name of the variable to check.
    - ``expected``: The expected value.
    If a string, checks equality.
    If an integer, checks that the variable is greater than or equal.
    If ``None``, checks that the variable is not set.

    **Returns**
    - ``True`` if the variable matches the expected condition.
    - ``False`` otherwise.

    **Example**

    .. code-block:: json

        "conditions": [
            "is variable player_gold 100"
        ]
    """

    name = "variable"
    var_name: str
    expected: str | int | None = None

    def test_with_monster(self, session: Session, target: Monster) -> bool:
        var_name = self.var_name
        expect = self.expected

        player = session.player
        if type(expect) is str:
            return bool(player.game_variables.get(var_name) == expect)
        elif type(expect) is int:
            return bool(player.game_variables.get(var_name) >= expect)
        else:
            return not player.game_variables.get(var_name)
