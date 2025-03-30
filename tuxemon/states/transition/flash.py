# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

import pygame

from tuxemon import prepare
from tuxemon.graphics import ColorLike
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class FlashTransition(State):
    """The state responsible for the battle transitions."""

    force_draw = True

    def __init__(
        self,
        color: ColorLike = prepare.WHITE_COLOR,
        flash_time: float = 0.2,
        max_flash_count: int = 7,
    ) -> None:
        """
        Parameters:
            color: The color to use for the flash effect. Defaults to white.
            flash_time: The time in seconds between flashes. Defaults to 0.2
                seconds.
            max_flash_count: The maximum number of times the flash effect will
                repeat. Defaults to 7.
        """
        super().__init__()
        logger.info("Initializing battle transition")
        self.flash_time = flash_time
        self.flash_state = "up"
        self.transition_alpha = 0.0
        self.max_flash_count = max_flash_count
        self.flash_count = 0
        self.client.rumble.rumble(-1, length=1.5)
        self.color = color

    def resume(self) -> None:
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill(self.color)

    def update(self, time_delta: float) -> None:
        """
        Update function for state.

        Parameters:
            time_delta: Time since last update in seconds

        """
        logger.info("Battle transition!")

        if self.flash_state == "up":
            self.transition_alpha = min(
                255,
                self.transition_alpha + 255 * (time_delta / self.flash_time),
            )
        elif self.flash_state == "down":
            self.transition_alpha = max(
                0, self.transition_alpha - 255 * (time_delta / self.flash_time)
            )

        if self.transition_alpha >= 255:
            self.flash_state = "down"
            self.flash_count += 1
        elif self.transition_alpha <= 0:
            self.flash_state = "up"
            self.flash_count += 1

        if self.flash_count > self.max_flash_count:
            logger.info(
                f"Flashed {self.flash_count} times. Stopping transition."
            )
            self.client.pop_state()

    def draw(self, surface: pygame.surface.Surface) -> None:
        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(int(self.transition_alpha))
        surface.blit(self.transition_surface, (0, 0))

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # prevent other states from getting input
        return None
