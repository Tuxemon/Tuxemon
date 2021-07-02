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

from __future__ import annotations
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final


class SetVariableActionParameters(NamedTuple):
    var_list: str


@final
class SetVariableAction(EventAction[SetVariableActionParameters]):
    """Sets the key in the player.game_variables dictionary.

    Valid Parameters: variable_name:value
    """

    name = "set_variable"
    param_class = SetVariableActionParameters

    def start(self) -> None:
        player = self.session.player

        # Split the variable into a key: value pair
        var_list = self.parameters[0].split(":")
        var_key = str(var_list[0])
        var_value = str(var_list[1])

        # Append the game_variables dictionary with the key: value pair
        player.game_variables[var_key] = var_value
