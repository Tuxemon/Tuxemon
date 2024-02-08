# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class FormatVariableAction(EventAction):
    """
    Format the value of a variable from the game (eg. float or int).

    Script usage:
        .. code-block::

            format_variable <variable>,<type_format>[,rounding]

    Script parameters:
        variable: The variable to format.
        type_format: Kind of format (float or int).
        rounding: How many decimal digits (if a float).

    """

    name = "format_variable"
    variable: str
    type_format: str
    rounding: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        key = self.variable
        type_format = self.type_format
        _rounding = self.rounding
        value = player.game_variables.get(key, None)
        if value is None:
            logger.error(f"Game variable {key} doesn't exist")
            return
        if type_format not in ("int", "float"):
            logger.error(f"{type_format} isn't 'float' or 'int'")
            return
        if type_format == "int":
            player.game_variables[key] = int(value)
        elif type_format == "float":
            if _rounding is None:
                player.game_variables[key] = float(value)
            else:
                _value = float(value)
                player.game_variables[key] = round(_value, _rounding)
        else:
            player.game_variables[key] = value
