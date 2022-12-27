# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster
from tuxemon.npc import NPC


@dataclass
class VariableCondition(ItemCondition):
    """Checks against the variables of the context.
    Accepts two parameters; variable name and expected value.
    """

    name = "variable"
    var_name: str
    context: Union[NPC, Monster]
    expected: Union[str, int, None] = None

    def test(self, target: Monster) -> bool:
        var_name = self.var_name
        expect = self.expected

        if self.context == "target":
            context = target
        else:
            context = self.user

        if type(expect) is str:
            return context.game_variables[var_name] == expect
        elif type(expect) is int:
            return context.game_variables[var_name] >= expect
        else:
            return not context.game_variables[var_name]
