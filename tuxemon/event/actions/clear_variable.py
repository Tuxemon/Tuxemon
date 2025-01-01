# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class ClearVariableAction(EventAction):
    """
    Clear the value of a variable from the game.

    Script usage:
        .. code-block::

            clear_variable <variable>

    Script parameters:
        variable: The variable to clear.

    """

    name = "clear_variable"
    variable: str

    def start(self) -> None:
        player = self.session.player
        key = self.variable
        player.game_variables.pop(key, None)
