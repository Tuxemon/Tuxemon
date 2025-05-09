# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

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
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        world = session.client.get_state_by_name(WorldState)
        world.movement.stop_char(character)
