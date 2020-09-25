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


from tuxemon.core.item.itemcondition import ItemCondition


class TypeCondition(ItemCondition):
    """Compares the target Monster's type1 and type2 against the given types.
    Returns true if either is equal to any of the listed types.
    """
    name = "type"
    valid_parameters = [
        (str, "type1"),
        ((str, None), "type2"),
        ((str, None), "type3"),
        ((str, None), "type4"),
        ((str, None), "type5")
    ]

    def test(self, target):
        ret = False
        if target.type1 is not None:
            ret = any(target.type1.lower() == p.lower() for p in self.parameters)
        if target.type2 is not None:
            ret = ret or any(target.type2.lower() == p.lower() for p in self.parameters)

        return ret
