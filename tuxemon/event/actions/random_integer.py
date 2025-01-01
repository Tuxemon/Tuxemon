# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from random import randint
from typing import final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class RandomIntegerAction(EventAction):
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
    var: str
    lower_bound: int
    upper_bound: int

    def start(self) -> None:
        player = self.session.player

        # Append the game_variables dictionary with a random number between
        # upper and lower bound, inclusive:
        number = randint(self.lower_bound, self.upper_bound)
        player.game_variables[self.var] = str(number)
        logger.info(f"Game variable: {self.var}:{number}")
