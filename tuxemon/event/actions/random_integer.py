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
from random import randint
from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)

class RandomIntegerActionParameters(NamedTuple):
    var: str
    lower_bound: int
    upper_bound: int


@final
class RandomIntegerAction(EventAction[RandomIntegerActionParameters]):
    """
    Randomly choose an integer between 2 numbers (inclusive), and set the key in the
    player.game_variables dictionary to be this value.

    For example, 'random_integer xyz,1,6' will set the value of the game variable
    'xyz' to be either 1, 2, 3, 4, 5, or 6.

    Script usage:
        .. code-block::

            random_integer <variable>,<lower_bound>,<upper_bound>

    Script parameters:
        variable: Name of the variable.
        lower_bound: Lower bound of range to return an integer between (inclusive)
        upper_bound: Upper bound of range to return an integer between (inclusive)

    """

    name = "random_integer"
    param_class = RandomIntegerActionParameters

    def start(self) -> None:
        player = self.session.player

        var, lower_bound, upper_bound = self.parameters

        # Append the game_variables dictionary with a random number between
        # upper and lower bound, inclusive:
        player.game_variables[var] = randint(lower_bound, upper_bound)
