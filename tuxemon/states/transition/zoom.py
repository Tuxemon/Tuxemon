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


class ZoomOutTransition(State):
    """The state responsible for the zoom out transitions."""

    force_draw = True

    def __init__(
        self, image: pygame.Surface, scale: float = 0.1, speed: float = 0.5
    ) -> None:
        """
        Parameters:
            image: The image to be used for the zoom out effect.
            scale: The initial scale factor of the image. Defaults to 0.1,
                meaning the image will start at 10% of its original size.
            speed: The rate at which the image scales down per second.
                Defaults to 0.5, meaning the image will decrease in size by 50%
                every second.
        """
        super().__init__()
        logger.info("Initializing Zoom Out transition")
        self.image = image
        self.scale = scale
        self.speed = speed  # scale factor per second

    def update(self, time_delta: float) -> None:
        if self.scale < 1.0:
            self.scale += self.speed * time_delta
        else:
            self.scale = 1.0

        if self.scale >= 1.0:
            logger.info("Zoom Out transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.Surface) -> None:
        scaled_image = pygame.transform.scale(
            self.image,
            (
                int(self.image.get_width() * self.scale),
                int(self.image.get_height() * self.scale),
            ),
        )
        rect = scaled_image.get_rect(
            center=(
                prepare.SCREEN.get_width() // 2,
                prepare.SCREEN.get_height() // 2,
            )
        )
        surface.blit(scaled_image, rect)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None


class ZoomInTransition(State):
    """The state responsible for the zoom in transitions."""

    force_draw = True

    def __init__(
        self, image: pygame.Surface, scale: float = 1.0, speed: float = 0.5
    ) -> None:
        """
        Parameters:
            image: The image to be used for the zoom in effect.
            scale: The initial scale factor of the image. Defaults to 1.0,
                meaning the image will start at 100% of its original size.
            speed: The rate at which the image scales down per second.
                Defaults to 0.5, meaning the image will decrease in size by 50%
                every second.
        """
        super().__init__()
        logger.info("Initializing Zoom In transition")
        self.image = image
        self.scale = scale
        self.speed = speed  # scale factor per second

    def update(self, time_delta: float) -> None:
        if self.scale > 0.1:
            self.scale -= self.speed * time_delta
        else:
            self.scale = 0.1

        if self.scale <= 0.1:
            logger.info("Zoom In transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.Surface) -> None:
        scaled_image = pygame.transform.scale(
            self.image,
            (
                int(self.image.get_width() * self.scale),
                int(self.image.get_height() * self.scale),
            ),
        )
        rect = scaled_image.get_rect(
            center=(
                prepare.SCREEN.get_width() // 2,
                prepare.SCREEN.get_height() // 2,
            )
        )
        surface.blit(scaled_image, rect)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
