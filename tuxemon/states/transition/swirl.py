# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

import pygame

from tuxemon import prepare
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class SwirlTransition(State):
    """The state responsible for the swirl transitions."""

    force_draw = True

    def __init__(
        self, image: pygame.Surface, scale: float = 1.2, speed: float = 50.0
    ) -> None:
        """
        Parameters:
            image: The image to be used for the swirl effect.
            scale: The initial scale factor of the image. Defaults to 1.2,
                meaning the image will start at 120% of its original size.
            speed: The rate of rotation in degrees per second. Defaults to 50.
        """
        super().__init__()
        logger.info("Initializing Swirl transition")
        self.image = image
        self.center_x = prepare.SCREEN.get_width() // 2
        self.center_y = prepare.SCREEN.get_height() // 2
        self.angle = 0.0
        self.scale = scale
        self.speed = speed

    def update(self, time_delta: float) -> None:
        self.angle += self.speed * time_delta
        self.scale += 0.01 * time_delta
        if self.angle > 360:
            logger.info("Swirl transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        scaled_image = pygame.transform.scale(
            rotated_image,
            (
                int(rotated_image.get_width() * self.scale),
                int(rotated_image.get_height() * self.scale),
            ),
        )
        rect = scaled_image.get_rect(center=(self.center_x, self.center_y))
        surface.blit(scaled_image, rect)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
