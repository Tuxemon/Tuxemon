# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SaveTimestampAction(EventAction):
    """
    Saves the current Unix timestamp (in seconds) into a game variable.

    Script usage:
        .. code-block::

            save_timestamp <variable>

    Script parameters:
        variable: The name of the game variable to store the timestamp in.
    """

    name = "save_timestamp"
    variable: str

    def start(self, session: Session) -> None:
        timestamp = time.time()
        session.player.game_variables.set(self.variable, timestamp)
        logger.info(
            f"Saved timestamp {timestamp} to variable '{self.variable}'"
        )
