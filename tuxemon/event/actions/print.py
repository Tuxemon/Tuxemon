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
import logging

from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, Optional

logger = logging.getLogger(__name__)


class PrintActionParameters(NamedTuple):
    variable: Optional[str]


class PrintAction(EventAction[PrintActionParameters]):
    """
    Print the current value of a game variable.

    If no variables are specified, print out values of all game variables.

    Script usage:
        .. code-block::

            print
            print <variable>

        Script parameters:
            variable: Optional, prints out the value of this variable.

    """

    name = "print"
    param_class = PrintActionParameters

    def start(self) -> None:
        player = self.session.player

        variable = self.parameters.variable
        if variable and variable > "":
            if variable in player.game_variables:
                print(f"{variable}: {player.game_variables[variable]}")
            else:
                print(f"'{variable}' has not been set yet by map actions.")
        else:
            print(player.game_variables)
