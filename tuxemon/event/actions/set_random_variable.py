# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetRandomVariableAction(EventAction):
    """
    Sets a key in the player's `game_variables` dictionary to a randomly
    selected value from a specified list. Values can be repeated or
    weighted to influence selection probability.

    Script usage:
        .. code-block::

            set_random_variable <variable>,<value1>:<value2>:<value3>

        You can also use weighted values:
            set_random_variable <variable>,<apple=1>:<banana=3>:<cherry=2>

    Script parameters:
        variable: The name of the game variable to set.
        values: A colon-separated string of values to choose from.
            - Repeated values increase their selection chance.
            - Alternatively, use `value=weight` to assign explicit weights.
    """

    name = "set_random_variable"
    var_key: str
    var_value: str

    def start(self, session: Session) -> None:
        player = session.player

        raw_entries = self.var_value.split(":")
        options = []
        weights = []

        for entry in raw_entries:
            if "=" in entry:
                value, weight = entry.split("=", 1)
                options.append(value)
                try:
                    weights.append(int(weight))
                except ValueError:
                    weights.append(1)  # fallback if weight isn't a valid int
            else:
                options.append(entry)
                weights.append(1)  # default weight

        random_value = random.choices(options, weights)[0]
        player.game_variables.set(self.var_key, random_value)
        logger.info(
            f"Game variable '{self.var_key}' set to '{random_value}' (weighted)"
        )
