# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


class CameraMode(Enum):
    FIXED = "fixed"
    FREE_ROAMING = "free_roaming"


@final
@dataclass
class CameraPositionAction(EventAction):
    """
    Move the camera on a coordinate.

    Script usage:
        .. code-block::

            camera_position <x>,<y>,<mode>

    Script parameters:
        x,y: the coordinates where the camera needs to be centered.
        mode: the camera mode, either "fixed" or "free_roaming", default "fixed"

    """

    name = "camera_position"
    x: Optional[int] = None
    y: Optional[int] = None
    mode: Optional[str] = "fixed"

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        map_size = self.session.client.map_size

        if self.x is not None and self.y is not None:
            if world.boundary_checker.is_within_boundaries((self.x, self.y)):
                if world.camera.follows_entity:
                    world.camera.unfollow()
                if self.mode in [m.value for m in CameraMode]:
                    world.camera.free_roaming_enabled = (
                        self.mode == CameraMode.FREE_ROAMING.value
                    )
                else:
                    logger.warning(
                        f"Invalid camera mode: {self.mode}. Defaulting to fixed."
                    )
                    world.camera.free_roaming_enabled = False
                world.camera.move(self.x, self.y)
                logger.info(
                    f"Camera has been set to ({self.x, self.y}) with mode {self.mode}"
                )
            else:
                logger.error(
                    f"({self.x, self.y}) is outside the map bounds {map_size}"
                )
        else:
            world.camera.reset_to_entity_center()
            logger.info("Camera has been reset to entity's center")
