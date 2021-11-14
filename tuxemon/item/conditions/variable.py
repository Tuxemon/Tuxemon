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
# Contributor(s):
#
# Adam Chevalier <chevalieradam2@gmail.com>
#

from __future__ import annotations
from tuxemon.item.itemcondition import ItemCondition
from typing import NamedTuple, Union
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.script_context import ScriptContext
from tuxemon.item.item import ItemContext


class VariableConditionParameters(NamedTuple):
    var_name: str
    expected: Union[str, int, None]


class VariableCondition(ItemCondition[VariableConditionParameters]):
    """Checks against the variables of the context.
    Accepts two parameters; variable name and expected value.
    """

    name = "variable"
    param_class = VariableConditionParameters

    def test(self, context: ScriptContext) -> bool:

        if not isinstance(context, ItemContext):
            return False

        var_name = self.parameters.var_name
        expect = self.parameters.expected

        subcontext: Union[NPC, Monster]
        if self.context == "target":
            subcontext = context.target
        else:
            subcontext = self.user

        if type(expect) is str:
            return subcontext.game_variables[var_name] == expect
        elif type(expect) is int:
            return subcontext.game_variables[var_name] >= expect
        else:
            return not subcontext.game_variables[var_name]
