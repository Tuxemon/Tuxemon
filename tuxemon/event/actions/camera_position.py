# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.camera import Camera
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
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

    def start(self, session: Session) -> None:
        world = session.client.get_state_by_name(WorldState)
        camera = world.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return
        if self.x is not None and self.y is not None:
            map_size = session.client.map_manager.map_size
            if not session.client.boundary.is_within_boundaries(
                (self.x, self.y)
            ):
                logger.error(
                    f"({self.x, self.y}) is outside the map bounds {map_size}"
                )
                return
            self._move_camera(camera, self.x, self.y)
        else:
            self._reset_camera(camera)

    def _move_camera(self, camera: Camera, x: int, y: int) -> None:
        if camera.follows_entity:
            camera.unfollow()
        camera.set_position(x, y)
        logger.info(f"Camera has been set to ({x, y})")

    def _reset_camera(self, camera: Camera) -> None:
        camera.reset_to_entity_center()
        logger.info("Camera has been reset to entity's center")
