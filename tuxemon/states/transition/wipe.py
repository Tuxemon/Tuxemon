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


class WipeTransition(State):
    """The state responsible for the wipe transitions."""

    force_draw = True

    def __init__(
        self,
        image: pygame.Surface,
        direction: str,
        speed: int = 250,
        color: ColorLike = prepare.BLACK_COLOR,
    ) -> None:
        """
        Parameters:
            image: The image to be used for the wipe effect.
            direction: The direction. Can be either "right", "left", "up" or
                "down"
            speed: The pixels per second. Defaults to 250.
            color: The color to use for the flash effect. Defaults to black.
        """
        super().__init__()
        logger.info("Initializing Wipe transition")
        self.image = image
        self.direction = direction
        self.wipe_x = 0.0
        self.wipe_y = 0.0
        self.color = color
        self.speed = speed
        self.height = prepare.SCREEN.get_height()
        self.width = prepare.SCREEN.get_width()

    def update(self, time_delta: float) -> None:
        self.update_wipe_position(time_delta)
        self.check_boundary()

    def update_wipe_position(self, time_delta: float) -> None:
        direction_map = {
            "left": (1, 0),
            "right": (-1, 0),
            "up": (0, 1),
            "down": (0, -1),
        }
        dx, dy = direction_map[self.direction]
        self.wipe_x += dx * self.speed * time_delta
        self.wipe_y += dy * self.speed * time_delta

    def check_boundary(self) -> None:
        if (
            self.direction in ["left", "right"]
            and abs(self.wipe_x) >= self.width
        ) or (
            self.direction in ["up", "down"]
            and abs(self.wipe_y) >= self.height
        ):
            logger.info("Wipe transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, (0, 0))
        if self.direction in ["left", "right"]:
            pygame.draw.rect(
                surface, self.color, (self.wipe_x, 0, self.width, self.height)
            )
        else:
            pygame.draw.rect(
                surface, self.color, (0, self.wipe_y, self.width, self.height)
            )

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
