# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import CAMERA_SHAKE_RANGE
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraShakeAction(EventAction):
    """
    Shake the camera with a precise intensity and duration.

    Script usage:
        .. code-block::

            camera_shake <intensity>,<duration>

    Script parameters:
        intensity: The magnitude of the shake effect. A higher value results
            in a more pronounced shake, while a lower value produces
            a subtler effect (min 0.0, max 3.0).
        duration: The length of time (in seconds) that the shake effect
            should last. The method calculates the number of frames
            to shake based on an assumed frame rate.
    """

    name = "camera_shake"
    intensity: float
    duration: float

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        lower, upper = CAMERA_SHAKE_RANGE
        if not lower <= self.intensity <= upper:
            logger.error(
                f"{self.intensity} must be between {lower} and {upper}",
            )
        camera = world.camera_manager.get_active_camera()
        if camera is None:
            logger.error("No active camera found.")
            return
        camera.shake(self.intensity, self.duration)
        logger.info("Camera is shaking!")
