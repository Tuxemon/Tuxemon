# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from random import randint
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RandomIntegerAction(EventAction):
    """
    Randomly chooses an integer between two numbers (inclusive) and sets a key in
    the player's game_variables dictionary to this value.

    For example, 'random_integer xyz,1,6' will set the value of the game variable
    'xyz' to be a random integer from 1, 2, 3, 4, 5, or 6.

    Script usage:
        .. code-block::

            random_integer <variable>,<lower_bound>,<upper_bound>

    Script parameters:
        variable: Name of the variable to set.
        lower_bound: The inclusive lower bound of the integer range.
        upper_bound: The inclusive upper bound of the integer range.
    """

    name = "random_integer"
    var: str
    lower_bound: int
    upper_bound: int

    def start(self, session: Session) -> None:

        if self.lower_bound > self.upper_bound:
            logger.error(
                f"Invalid range for 'random_integer'. Lower bound ({self.lower_bound}) "
                f"cannot be greater than the upper bound ({self.upper_bound})."
            )
            self.stop()
            return

        player = session.player
        random_value = randint(self.lower_bound, self.upper_bound)
        player.game_variables.set(self.var, str(random_value))
        logger.info(f"Game variable: '{self.var}' set to {random_value}")
