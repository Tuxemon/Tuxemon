# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class CharWalkAction(EventAction):
    """
    Set the character movement speed to the global walk speed.

    Script usage:
        .. code-block::

            char_walk <character>

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").

    """

    name = "char_walk"
    character: str

    def start(self) -> None:
        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        character.moverate = self.session.client.config.player_walkrate
