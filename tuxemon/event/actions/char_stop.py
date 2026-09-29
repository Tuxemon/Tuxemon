# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class CharStopAction(EventAction):
    """
    Make the character stop moving.

    Script usage:
        .. code-block::

            char_stop <character>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
    """

    name = "char_stop"
    character: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return
        session.client.movement_manager.stop_char(character)
