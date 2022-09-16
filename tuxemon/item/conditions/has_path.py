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

from typing import NamedTuple

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


class HasPathConditionParameters(NamedTuple):
    expected: str


class HasPathCondition(ItemCondition[HasPathConditionParameters]):
    """
    Checks against the creature's evolution paths.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "has_path"
    param_class = HasPathConditionParameters

    def test(self, target: Monster) -> bool:
        expect = self.parameters.expected

        return any(d['path'] == expect for d in target.evolutions)
