# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any, ClassVar

from pygame import draw as pg_draw
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class MosaicTransition(State):
    """The state responsible for the mosaic transitions."""

    name: ClassVar[str] = "MosaicTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        duration: float = 1.0,
        tile_size: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
            tile_size: The size of the mosaic tile. Defaults to 10.
        """
        super().__init__(client=client, **kwargs)
        logger.info("Initializing Mosaic transition")
        self.duration = duration
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.tile_size = tile_size
        self.tiles: list[Rect] = []
        self.tile_surfaces: list[Surface] = []
        self.resume()

    def resume(self) -> None:
        self.screenshot = Surface.copy(self.client.context.screen)
        for x in range(0, self.screenshot.get_width(), self.tile_size):
            for y in range(0, self.screenshot.get_height(), self.tile_size):
                rect = Rect(x, y, self.tile_size, self.tile_size)
                self.tiles.append(rect)
                self.tile_surfaces.append(self.screenshot.subsurface(rect))

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if self.elapsed_time > self.duration:
            logger.info("Mosaic transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        for i, tile in enumerate(self.tiles):
            if random.random() < self.elapsed_time / self.duration:
                surface.blit(self.tile_surfaces[i], tile)
            else:
                pg_draw.rect(surface, (0, 0, 0), tile)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # prevent other states from getting input
        return None
