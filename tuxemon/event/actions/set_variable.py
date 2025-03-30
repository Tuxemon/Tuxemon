# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetVariableAction(EventAction):
    """
    Set the key in the player.game_variables dictionary.

    Script usage:
        .. code-block::

            set_variable <variable>:<value>

    Script parameters:
        variable: Name of the variable.
        value: Value of the variable
    """

    name = "set_variable"
    var_list: str

    def start(self) -> None:
        player = self.session.player

        # Split the variable into a key: value pair
        var_list = self.var_list.split(":")
        var_key = str(var_list[0])
        var_value = str(var_list[1])

        # Append the game_variables dictionary with the key: value pair
        player.game_variables[var_key] = var_value
