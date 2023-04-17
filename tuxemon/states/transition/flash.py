# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

import pygame

from tuxemon import prepare
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class FlashTransition(State):
    """The state responsible for the battle transitions."""

    force_draw = True

    def __init__(self) -> None:
        super().__init__()
        logger.info("Initializing battle transition")
        self.flash_time = 0.2  # Time in seconds between flashes
        self.flash_state = "up"
        self.transition_alpha = 0.0
        self.max_flash_count = 7
        self.flash_count = 0
        self.client.rumble.rumble(-1, length=1.5)

    def resume(self) -> None:
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill((255, 255, 255))

    def update(self, time_delta: float) -> None:
        """
        Update function for state.

        Parameters:
            time_delta: Time since last update in seconds

        """
        logger.info("Battle transition!")

        # self.battle_transition_alpha
        if self.flash_state == "up":
            self.transition_alpha += 255 * (time_delta / self.flash_time)

        elif self.flash_state == "down":
            self.transition_alpha -= 255 * (time_delta / self.flash_time)

        if self.transition_alpha >= 255:
            self.flash_state = "down"
            self.flash_count += 1

        elif self.transition_alpha <= 0:
            self.flash_state = "up"
            self.flash_count += 1

        # If we've hit our max number of flashes, stop the battle
        # transition animation.
        if self.flash_count > self.max_flash_count:
            logger.info(
                "Flashed "
                + str(self.flash_count)
                + " times. Stopping transition.",
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
