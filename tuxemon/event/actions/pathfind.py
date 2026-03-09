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
class PathfindAction(EventAction):
    """
    Pathfind the player / npc to the given location.

    This action blocks until the destination is reached.

    Script usage:
        .. code-block::

            pathfind <npc_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
    """

    name = "pathfind"
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int

    def start(self, session: Session) -> None:
        self.moving_entity = session.get_npc(self.npc_slug)
        if self.moving_entity is None:
            logger.warning(
                "PathfindAction skipped: entity '%s' not found.",
                self.npc_slug,
            )
            self.stop()
            return

        destination = (self.tile_pos_x, self.tile_pos_y)
        self.moving_entity.pathfind(destination)

    def update(self, session: Session, dt: float) -> None:
        if self.moving_entity is None:
            self.stop()
            return
        if not (self.moving_entity.moving or self.moving_entity.path):
            self.stop()
