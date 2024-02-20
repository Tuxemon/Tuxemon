# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class FormatVariableAction(EventAction):
    """
    Format the value of a variable from the game (eg. float or int).
    By default the game variable is a dict[str, Any].

    Script usage:
        .. code-block::

            format_variable <variable>,<type_format>

    Script parameters:
        variable: The variable to format.
        type_format: Kind of format (float or int).

    eg. "format_variable name_variable,int"

    """

    name = "format_variable"
    variable: str
    type_format: str

    def start(self) -> None:
        player = self.session.player
        key = self.variable
        type_format = self.type_format
        value = player.game_variables.get(key, None)
        if value is None:
            logger.error(f"Game variable {key} doesn't exist")
            return
        _formats = ["int", "float", "-int", "-float"]
        if type_format not in _formats:
            raise ValueError(f"{type_format} isn't 'float' or 'int'")
        if type_format == "int":
            player.game_variables[key] = int(value)
        elif type_format == "-int":
            player.game_variables[key] = -int(value)
        elif type_format == "float":
            player.game_variables[key] = float(value)
        elif type_format == "-float":
            player.game_variables[key] = -float(value)
        else:
            player.game_variables[key] = value
