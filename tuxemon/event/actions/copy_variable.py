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
class CopyVariableAction(EventAction):
    """
    Copy the value of var2 into var1 (e.g. var1 = var 2).

    Script usage:
        .. code-block::

            copy_variable <var1>,<var2>

    Script parameters:
        var1: The variable to copy to.
        var2: The variable to copy from.

    """

    name = "copy_variable"
    var1: str
    var2: str

    def start(self) -> None:
        player = self.session.player
        first = self.var1
        second = self.var2
        player.game_variables[first] = player.game_variables[second]
