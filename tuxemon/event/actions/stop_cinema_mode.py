# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class StopCinemaModeAction(EventAction):
    """
    Stop cinema mode by animating black bars back to the normal aspect ratio.

    Script usage:
        .. code-block::

            stop_cinema_mode

    """

    name = "stop_cinema_mode"

    def start(self) -> None:
        world = self.session.client.current_state
        assert isinstance(world, WorldState)
        if world.cinema_state == "on":
            logger.info("Turning off cinema mode")
            world.cinema_state = "turning off"
