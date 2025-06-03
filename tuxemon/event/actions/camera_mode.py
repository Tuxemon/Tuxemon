# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class CameraMode(Enum):
    FIXED = "fixed"
    FREE_ROAMING = "free_roaming"


@final
@dataclass
class CameraModeAction(EventAction):
    """
    Change camera mode: freeroaming or fixed.

    Script usage:
        .. code-block::

            camera_mode <mode>

    Script parameters:
        mode: The mode of the camera: 'free_roaming' or 'fixed'.
    """

    name = "camera_mode"
    mode: str

    def start(self, session: Session) -> None:
        camera = session.client.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return
        mode = CameraMode(self.mode)
        if mode == CameraMode.FREE_ROAMING:
            camera.free_roaming_enabled = True
            if camera.follows_entity:
                camera.unfollow()
        else:
            camera.reset_to_entity_center()
            camera.free_roaming_enabled = False
        logger.info(f"Camera mode set to {mode}")
