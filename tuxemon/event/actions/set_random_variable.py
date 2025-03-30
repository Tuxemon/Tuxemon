# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetRandomVariableAction(EventAction):
    """
    Set the key in the player.game_variables dictionary
    with a random value.

    Script usage:
        .. code-block::

            set_random_variable <variable>,<value>:<value>

    Script parameters:
        variable: Name of the variable.
        values: Multiple values of the variable separated
        with ":".

    """

    name = "set_random_variable"
    var_key: str
    var_value: str

    def start(self) -> None:
        player = self.session.player

        # Split the values
        value: str = ""
        values: list[str] = []
        if self.var_value.find(":"):
            values = self.var_value.split(":")
            value = random.choice(values)
        else:
            value = self.var_value

        # Append the game_variables dictionary with the key: value pair
        player.game_variables[self.var_key] = value
