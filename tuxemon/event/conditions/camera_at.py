# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.camera.camera import unproject
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.tools import compare

logger = logging.getLogger(__name__)


@dataclass
class CameraAtCondition(EventCondition):
    """
    Check to see if the camera is at the position on the map.

    Script usage:
        .. code-block::

            is camera_at <tile_pos_x>,<tile_pos_y>

    Script parameters:
        pos_x: X position of the camera.
        pos_y: Y position of the camera.
    """

    name: ClassVar[str] = "camera_at"
    pos_x: int
    pos_y: int

    def test(self, session: Session) -> bool:
        map_size = session.client.map_manager.map_size
        camera = session.client.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return False
        camera_pos = camera.get_position()
        cx, cy = unproject(
            session.client.context, (camera_pos.x, camera_pos.y)
        )
        if not session.client.boundary.is_within_boundaries(
            (self.pos_x, self.pos_y)
        ):
            logger.error(
                f"({self.pos_x, self.pos_y}) is outside the map bounds {map_size}"
            )
            return False
        return compare("equals", cx, self.pos_x) and compare(
            "equals", cy, self.pos_y
        )
