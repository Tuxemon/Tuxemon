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


class VariableCondition(ItemCondition):
    """Checks against the variables of the context.
    Accepts two parameters; variable name and expected value.
    """
    name = "variable"
    valid_parameters = [
        (str, "var_name"),
        ((str, int, None), "expected")
    ]

    def test(self, target):
        var_name = self.parameters.var_name
        expect = self.parameters.expected

        if self.context == 'target':
            context = target
        else:
            context = self.user

        if type(expect) is str:
            return context.game_variables[var_name] == expect
        elif type(expect) is int:
            return context.game_variables[var_name] >= expect
        elif not expect:
            return not context.game_variables[var_name]
