# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

import pygame

from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class PixelationTransition(State):
    """The state responsible for the pixelation transitions."""

    force_draw = True

    def __init__(
        self, duration: float = 1.0, scale_factor: float = 10.0
    ) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
            scale_factor: The level of pixelation or blockiness applied
                to the screen, with higher values resulting in a more
                extreme effect.
        """
        super().__init__()
        logger.info("Initializing Pixelation transition")
        self.duration = duration
        self.scale_factor = scale_factor
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
            logger.info("Pixelation transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.surface.Surface) -> None:
        small_screen = pygame.transform.scale(
            surface,
            (
                surface.get_width() // self.scale_factor,
                surface.get_height() // self.scale_factor,
            ),
        )
        surface.blit(
            pygame.transform.scale(small_screen, surface.get_size()), (0, 0)
        )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # prevent other states from getting input
        return None
