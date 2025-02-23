# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class StartCinemaModeAction(EventAction):
    """
    Start cinema mode by animating black bars to narrow the aspect ratio.

    For a cinematic experience, specify the width of the horizontal and
    vertical black bars as a ratio of the screen resolution.
    For example, to achieve a 2.39:1 aspect ratio on a 1920x1080 screen,
    you would set the horizontal ratio to 0.42 (1920 / 1080 * (16/9 - 2.39/1))
    and the vertical ratio to 0 (no vertical bars).

    By default only bar up and down.

    Script usage:
        .. code-block::

            start_cinema_mode [aspect_y_ratio][,aspect_x_ratio]

    Script parameters:
        aspect_y_ratio: The width of the horizontal black bars as a ratio of
            the screen resolution. Default standard cinema mode.
        aspect_x_ratio: The width of the vertical black bars as a ratio of
            the screen resolution. Default None.
    """

    name = "start_cinema_mode"
    aspect_y_ratio: Optional[float] = 2.39
    aspect_x_ratio: Optional[float] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        world.map_renderer.cinema_y_ratio = self.aspect_y_ratio
        world.map_renderer.cinema_x_ratio = self.aspect_x_ratio
