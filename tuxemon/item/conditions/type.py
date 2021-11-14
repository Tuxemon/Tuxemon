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
from tuxemon.script_context import ScriptContext
from tuxemon.item.item import ItemContext


class TypeConditionParameters(NamedTuple):
    type1: str
    type2: Union[str, None]
    type3: Union[str, None]
    type4: Union[str, None]
    type5: Union[str, None]


class TypeCondition(ItemCondition[TypeConditionParameters]):
    """
    Compares the target Monster's type1 and type2 against the given types.

    Returns true if either is equal to any of the listed types.

    """

    name = "type"
    param_class = TypeConditionParameters

    def test(self, context: ScriptContext) -> bool:
        if not isinstance(context, ItemContext):
            return False

        ret = False
        if context.target.type1 is not None:
            ret = any(
                context.target.type1.lower() == p.lower()
                for p in self.parameters if p is not None
            )
        if context.target.type2 is not None:
            ret = ret or any(
                context.target.type2.lower() == p.lower()
                for p in self.parameters if p is not None
            )

        return ret
