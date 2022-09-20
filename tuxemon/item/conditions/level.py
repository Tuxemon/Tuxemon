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

from operator import eq, ge, gt, le, lt
from typing import Callable, Mapping, NamedTuple, Optional

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster

cmp_dict: Mapping[Optional[str], Callable[[float, float], bool]] = {
    None: ge,
    "<": lt,
    "<=": le,
    ">": gt,
    ">=": ge,
    "==": eq,
    "=": eq,
}


class LevelConditionParameters(NamedTuple):
    comparison: str
    value: int


class LevelCondition(ItemCondition[LevelConditionParameters]):
    """
    Compares the target Monster's level against the given value.

    Example: To make an item only usable if a monster is at a
    certain level, you would use the condition "level target,<,5"

    """

    name = "level"
    param_class = LevelConditionParameters

    def test(self, target: Monster) -> bool:
        level = target.level
        operator = cmp_dict[self.parameters.comparison]
        level_reached = self.parameters.value

        return operator(level, level_reached)
