# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


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
        world = self.session.client.get_state_by_name(WorldState)
        world.cinema_x_ratio = None
        world.cinema_y_ratio = None
