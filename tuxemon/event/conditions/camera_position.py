# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass

from tuxemon.camera import unproject
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class CameraPositionCondition(EventCondition):
    """
    Check to see if the camera is at the position on the map.

    Script usage:
        .. code-block::

            is camera_position <tile_pos_x>,<tile_pos_y>

    Script parameters:
        pos_x: X position of the camera.
        pos_y: Y position of the camera.
    """

    name = "camera_position"

    def test(self, session: Session, condition: MapCondition) -> bool:
        map_size = session.client.map_manager.map_size
        pos_x = int(condition.parameters[0])
        pos_y = int(condition.parameters[1])
        camera = session.client.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return False
        cx, cy = unproject(camera.position)
        if not session.client.boundary.is_within_boundaries((pos_x, pos_y)):
            logger.error(
                f"({pos_x, pos_y}) is outside the map bounds {map_size}"
            )
            return False
        return compare("equals", cx, pos_x) and compare("equals", cy, pos_y)
