# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import Direction
from tuxemon.event.eventaction import EventAction
from tuxemon.map.map import get_coord_direction, get_direction, pairs
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
    direction: Direction | None = None
    distance: int | None = None

    def start(self, session: Session) -> None:
        client = session.client
        target_entity = session.client.get_npc(self.target_entity)
        assert target_entity
        self.moving_entity = session.client.get_npc(self.entity)
        assert self.moving_entity

        distance = max(1, self.distance or 1)

        approach_direction = self.direction or get_direction(
            self.moving_entity.tile_pos, target_entity.tile_pos
        )

        if self.direction is None:
            approach_direction = pairs(approach_direction)

        final_destination = get_coord_direction(
            target_entity.tile_pos,
            approach_direction,
            client.map_manager.map_size,
            distance,
        )

        self.moving_entity.set_facing(approach_direction)

        if self.moving_entity.tile_pos == final_destination:
            logger.info(
                f"Skipped: Moving entity {self.moving_entity.slug} is already at desired destination {final_destination}."
            )
            direction = get_direction(
                self.moving_entity.tile_pos, target_entity.tile_pos
            )
            self.moving_entity.set_facing(direction)
            self.stop()
            return

        self.moving_entity.pathfind(final_destination)

    def update(self, session: Session, dt: float) -> None:
        assert self.moving_entity
        if not (self.moving_entity.moving or self.moving_entity.path):
            self.stop()
