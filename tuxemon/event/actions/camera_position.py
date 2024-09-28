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
        world = self.session.client.get_state_by_name(WorldState)
        map_size = self.session.client.map_size
        roaming = False if self.roaming is None else True
        if world.boundary_checker.is_within_boundaries((self.x, self.y)):
            if world.camera.follows_player:
                world.camera.unfollow()
            world.camera.free_roaming_enabled = roaming
            world.camera.move(self.x, self.y)
            logger.info(f"Camera has been set to ({self.x, self.y})")
        else:
            logger.error(
                f"Coordinate ({self.x, self.y}) is outside the map bounds {map_size}"
            )
