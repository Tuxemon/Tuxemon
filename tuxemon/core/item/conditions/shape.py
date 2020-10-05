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


class ShapeCondition(ItemCondition):
    """Compares the target Monster's shape against the given types.
    Returns true if its equal to any of the listed types.
    """
    name = "shape"
    valid_parameters = [
        (str, "shape1"),
        ((str, None), "shape2"),
        ((str, None), "shape3"),
        ((str, None), "shape4"),
        ((str, None), "shape5")
    ]

    def test(self, target):
        ret = False
        if target.shape is not None:
            ret = any(target.shape.lower() == p.lower() for p in self.parameters)

        return ret
