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
class DelayedTeleportAction(EventAction):
    """
    Set teleport information.

    Teleport will be triggered during screen transition.

    Only use this if followed by a transition.

    Script usage:
        .. code-block::

            delayed_teleport <slug>,<map_name>,<position_x>,<position_y>

    Script parameters:
        map_name: Name of the map to teleport to.
        position_x: X position to teleport to.
        position_y: Y position to teleport to.

    """

    name = "delayed_teleport"
    character: str
    map_name: str
    position_x: int
    position_y: int

    def start(self, session: Session) -> None:
        world = session.client.get_state_by_name(WorldState)
        delayed_teleport = world.teleporter.delayed_teleport

        if delayed_teleport.is_active:
            logger.error("Stop, there is a teleport in progress")
            return

        char = get_npc(session, self.character)
        if char is None:
            logger.error(f"{self.character} not found")
            return

        delayed_teleport.char = char
        delayed_teleport.is_active = True
        delayed_teleport.mapname = self.map_name
        delayed_teleport.x = self.position_x
        delayed_teleport.y = self.position_y
