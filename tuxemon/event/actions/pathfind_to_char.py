# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import Direction
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import get_coord_direction, get_coords, get_direction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class PathfindToCharAction(EventAction):
    """
    Handles pathfinding movement where one entity navigates toward another
    with configurable direction and distance.

    Script usage:
        .. code-block::

            pathfind_to_char <target_entity>,<moving_entity>,
                                    [direction],[distance]

    Script parameters:
        target_entity: The target entity being approached
            (e.g. "character_maple").
        moving_entity: The entity that will move toward the target
            (e.g. "character_jimmy").
        direction: Determines approach direction
            (up, down, left, or right).
        distance: Number of tiles to maintain from the player
            (e.g. 2,3,4).
    """

    name = "pathfind_to_char"
    target_entity: str
    entity: str
    direction: Optional[Direction] = None
    distance: Optional[int] = None

    def start(self, session: Session) -> None:
        client = session.client
        target_entity = get_npc(session, self.target_entity)
        assert target_entity
        self.moving_entity = get_npc(session, self.entity)
        assert self.moving_entity

        distance = max(1, self.distance or 1)

        direction = self.direction or get_direction(
            self.moving_entity.tile_pos, target_entity.tile_pos
        )
        closest = get_coord_direction(
            self.moving_entity.tile_pos,
            direction,
            client.map_manager.map_size,
            distance,
        )

        self.moving_entity.set_facing(direction)

        tiles = get_coords(
            self.moving_entity.tile_pos, client.map_manager.map_size
        )
        if closest in tiles:
            logger.info(
                f"Skipped: Destination {closest} is adjacent to {self.moving_entity.tile_pos}."
            )
            return

        self.moving_entity.pathfind(closest)

    def update(self, session: Session) -> None:
        assert self.moving_entity
        if not (self.moving_entity.moving or self.moving_entity.path):
            self.stop()
