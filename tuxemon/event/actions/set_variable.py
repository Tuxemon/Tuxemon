# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetVariableAction(EventAction):
    """
    Updates the player's game variables by setting key-value pairs.

    Script usage:
        .. code-block::

            set_variable <variable>:<value>[,<variable>:<value>]

    Script parameters:
        variable: The name of the variable.
        value: The assigned value for the variable.

    This implementation supports multiple parameters, allowing multiple
    variable assignments in one call.
    """

    name = "set_variable"
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args: Any) -> None:
        super().__init__()
        self.raw_parameters = args

    def start(self) -> None:
        player = self.session.player
        for param in self.raw_parameters:
            var_key, _, var_value = param.partition(":")
            player.game_variables[var_key] = var_value
