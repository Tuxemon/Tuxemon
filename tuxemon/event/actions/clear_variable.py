# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ClearVariableAction(EventAction):
    """
    Removes specified variables from the player's stored variables.

    Script usage:
        .. code-block::

            clear_variable <variable1>[,variable2]

    Script parameters:
        variable: One or more variables to be removed.
    """

    name = "clear_variable"
    raw_parameters: Sequence[str] = field(init=False)

    def __init__(self, *args: Any) -> None:
        super().__init__()
        self.raw_parameters = args

    def start(self, session: Session) -> None:
        player = session.player
        for param in self.raw_parameters:
            if param not in player.game_variables:
                logger.error(f"Key '{param}' not found in game variables")
            player.game_variables.pop(param, None)
