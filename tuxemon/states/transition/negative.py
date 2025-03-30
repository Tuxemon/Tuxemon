# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

import pygame

from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class NegativeTransition(State):
    """The state responsible for the negative transitions."""

    force_draw = True

    def __init__(self, duration: float = 1.0) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
        """
        super().__init__()
        logger.info("Initializing negative transition")
        self.duration = duration
        self.start_time = 0.0
        self.elapsed_time = 0.0

    def update(self, time_delta: float) -> None:
        """
        Update function for state.

        Parameters:
            time_delta: Time since last update in seconds

        """
        self.elapsed_time += time_delta
        if self.elapsed_time > self.duration:
            logger.info("Negative colors transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.surface.Surface) -> None:
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                r, g, b, a = surface.get_at((x, y))
                r = 255 - r
                g = 255 - g
                b = 255 - b
                surface.set_at((x, y), (r, g, b, a))

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # prevent other states from getting input
        return None
