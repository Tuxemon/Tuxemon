# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraReset(EventAction):
    """
    Reset the camera (default player)

    Script usage:
        .. code-block::

            camera_reset

    """

    name = "camera_reset"

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        world.camera.reset_to_player_center()
