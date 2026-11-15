# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.teleporter import TeleportRequest

logger = logging.getLogger(__name__)


@final
@dataclass
class TeleportAction(EventAction):
    """
    Teleport a character to a specific map and tile coordinates.

    If a screen transition is in progress, the teleport will be queued
    and executed at the apex of the transition.

    Script usage:
        .. code-block::

            teleport <character>,<map_name>,<x>,<y>

    Script parameters:
        character: Slug of the character to teleport.
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
    """

    name = "teleport"
    character: str
    map_name: str
    x: int
    y: int

    def start(self, session: Session) -> None:
        teleport_queue = session.client.teleporter.teleport_queue

        char = session.client.get_npc(self.character)
        if char is None:
            logger.error(
                f"TeleportAction: Character '{self.character}' not found."
            )
            self.stop()
            return

        request = TeleportRequest(
            char=char,
            mapname=self.map_name,
            x=self.x,
            y=self.y,
            source_map=char.current_map,
            source_x=char.tile_pos[0],
            source_y=char.tile_pos[1],
        )

        if session.world.transition_manager.in_transition:
            teleport_queue.enqueue(request)
            logger.info(
                f"Queued teleport for '{char.slug}' to {self.map_name} ({self.x}, {self.y})"
            )
        else:
            session.client.teleporter.execute_teleport(char, request)
            logger.info(
                f"Teleported '{char.slug}' to {self.map_name} ({self.x}, {self.y})"
            )
        session.client.movement_manager.unlock_controls(char)
