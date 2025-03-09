# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraPositionAction(EventAction):
    """
    Move the camera on a coordinate.

    Script usage:
        .. code-block::

            camera_position <x>,<y>

    Script parameters:
        x,y: the coordinates where the camera needs to be centered.

    """

    name = "camera_position"
    x: Optional[int] = None
    y: Optional[int] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        if self.x is not None and self.y is not None:
            self._move_camera(world, self.x, self.y)
        else:
            self._reset_camera(world)

    def _move_camera(self, world: WorldState, x: int, y: int) -> None:
        map_size = self.session.client.map_size
        if not world.boundary_checker.is_within_boundaries((x, y)):
            logger.error(f"({x, y}) is outside the map bounds {map_size}")
            return
        camera = world.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return

        if camera.follows_entity:
            camera.unfollow()

        camera.set_position(x, y)
        logger.info(f"Camera has been set to ({x, y})")

    def _reset_camera(self, world: WorldState) -> None:
        camera = world.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return
        camera.reset_to_entity_center()
        logger.info("Camera has been reset to entity's center")
