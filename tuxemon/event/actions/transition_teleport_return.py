# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import Direction
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class TransitionTeleportReturnAction(EventAction):
    """
    Teleport a character back to their previously recorded location,
    using a screen transition.

    This action retrieves the last executed teleport request and sends
    the character back to its source map and coordinates. It must be
    used after a teleport that stored return data (e.g. source_map, source_x, source_y).

    Script usage:
        .. code-block::

            transition_teleport_return <character>,<facing>[,trans_time][,rgb]

    Script parameters:
        character: Either "player" or character slug name (e.g. "npc_maple").
        facing: One of "up", "down", "left", "right". Case-insensitive.
        trans_time: (Optional) Transition time in seconds. Default is 0.3.
        rgb: (Optional) Transition color in RGB format (e.g. "255:0:0" for red).
             Default is black (0,0,0).

    Requirements:
        - A previous teleport must have been executed and stored in
          `teleporter.last_teleport_request`.
        - The previous request must include valid source map and coordinates.

    Example:
        transition_teleport_return player,down,0.5,255:255:255
    """

    name = "transition_teleport_return"
    character: str
    facing: str
    trans_time: float | None = None
    rgb: str | None = None

    def start(self, session: Session) -> None:

        char = session.client.get_npc(self.character)
        if char is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        request = session.client.teleporter.last_teleport_request
        if not request:
            logger.error("No previous teleport request found.")
            self.stop()
            return

        if (
            not request.source_map
            or request.source_x is None
            or request.source_y is None
        ):
            logger.error(
                "Last teleport request is missing source location data."
            )
            self.stop()
            return

        try:
            facing_dir = Direction(self.facing.lower())
        except ValueError:
            logger.warning(f"Invalid facing direction: {self.facing}")
            self.stop()
            return

        char.set_facing(facing_dir)

        session.client.event_engine.execute_action(
            "transition_teleport",
            [
                self.character,
                request.source_map,
                request.source_x,
                request.source_y,
                self.trans_time,
                self.rgb,
            ],
        )
