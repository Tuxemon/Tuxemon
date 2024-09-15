# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraPosition(EventAction):
    """
    Move the camera on a coordinate.

    Script usage:
        .. code-block::

            camera_position x,y[,roaming]

    Script parameters:
        x,y: the coordinates where the camera needs to be centered.
        roaming: enables free roaming, default false

    """

    name = "camera_position"
    x: int
    y: int
    roaming: Optional[str] = None

    def start(self) -> None:
        map_size = self.session.client.map_size
        roaming = False if self.roaming is None else True
        if self.is_within_map_bounds(map_size):
            world = self.session.client.get_state_by_name(WorldState)
            if world.camera.follows_player:
                world.camera.unfollow()
            world.camera.free_roaming_enabled = roaming
            world.camera.move(self.x, self.y)
            logger.info(f"Camera has been set to ({self.x, self.y})")
        else:
            logger.error(
                f"Coordinate ({self.x, self.y}) is outside the map bounds {map_size}"
            )

    def is_within_map_bounds(self, map_size: tuple[int, int]) -> bool:
        return 0 <= self.x < map_size[0] and 0 <= self.y < map_size[1]
