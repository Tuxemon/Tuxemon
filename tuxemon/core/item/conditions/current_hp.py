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


from operator import eq, gt, lt, ge, le

from tuxemon.core.item.itemcondition import ItemCondition

cmp_dict = {
    None: ge,
    "<": lt,
    "<=": le,
    ">": gt,
    ">=": ge,
    "==": eq,
    "=": eq
}


class CurrentHitPointsCondition(ItemCondition):
    """Compares the target Monster's current hitpoints against the given value.
    If an integer is passed, it will compare against the number directly, if a 
    decimal between 0.0 and 1.0 is passed it will compare the current hp against
    the total hp.

    Example: To make an item only usable if a monster is at less than full health, you
    would use the condition "current_hp target,<,1.0"
    """

    name = 'current_hp'
    valid_parameters = [
        (str, 'comparison'),
        ((int, float), 'value')
    ]

    def test(self, target):
        lhs = target.current_hp
        op = cmp_dict[self.parameters.comparison]
        if type(self.parameters.value) is float:
            rhs = target.hp * self.parameters.value
        else:
            rhs = self.parameters.value

        return op(lhs, rhs)
