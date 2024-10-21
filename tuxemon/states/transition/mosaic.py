# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import Optional

import pygame

from tuxemon import prepare
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class MosaicTransition(State):
    """The state responsible for the mosaic transitions."""

    force_draw = True

    def __init__(self, duration: float = 1.0, tile_size: int = 10) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
            tile_size: The size of the mosaic tile. Defaults to 10.
        """
        super().__init__()
        logger.info("Initializing Mosaic transition")
        self.duration = duration
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.tile_size = tile_size
        self.tiles: list[pygame.Rect] = []
        self.tile_surfaces: list[pygame.Surface] = []
        self.resume()

    def resume(self) -> None:
        self.screenshot = pygame.Surface.copy(prepare.SCREEN)
        for x in range(0, self.screenshot.get_width(), self.tile_size):
            for y in range(0, self.screenshot.get_height(), self.tile_size):
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                self.tiles.append(rect)
                self.tile_surfaces.append(self.screenshot.subsurface(rect))

    def update(self, time_delta: float) -> None:
        """
        Update function for state.

        Parameters:
            time_delta: Time since last update in seconds

        """
        self.elapsed_time += time_delta
        if self.elapsed_time > self.duration:
            logger.info("Mosaic transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.surface.Surface) -> None:
        for i, tile in enumerate(self.tiles):
            if random.random() < self.elapsed_time / self.duration:
                surface.blit(self.tile_surfaces[i], tile)
            else:
                pygame.draw.rect(surface, (0, 0, 0), tile)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # prevent other states from getting input
        return None
