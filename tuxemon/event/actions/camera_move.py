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
class CameraMoveAction(EventAction):
    """
    Smoothly move the camera to a specific coordinate or reset it to its original position.

    Script usage:
        .. code-block::

            camera_move <time>,<x>,<y>

    Script parameters:
        time: the duration (in seconds) required for the camera to transition to the target position.
        x,y: the coordinates where the camera needs to be centered.
    """

    name = "camera_move"
    time: float
    x: Optional[int] = None
    y: Optional[int] = None

    def start(self, session: Session) -> None:
        world = session.client.get_state_by_name(WorldState)
        self.camera = world.camera_manager.get_active_camera()
        if self.camera is None:
            logger.error("No active camera found.")
            return
        if self.x is not None and self.y is not None:
            if not session.client.boundary.is_within_boundaries(
                (self.x, self.y)
            ):
                map_size = session.client.map_manager.map_size
                logger.error(
                    f"({self.x, self.y}) is outside the map bounds {map_size}"
                )
                return
            self._move_camera(self.camera, self.x, self.y)
        else:
            self._reset_camera(self.camera)

    def _move_camera(self, camera: Camera, x: int, y: int) -> None:
        if camera.follows_entity:
            camera.unfollow()
        camera.move_smoothly_to(x, y, self.time)
        logger.info(f"Camera has been moved to ({x, y})")

    def _reset_camera(self, camera: Camera) -> None:
        camera.smooth_reset_to_entity_center(self.time)
        logger.info("Camera has been reset to entity's center")
