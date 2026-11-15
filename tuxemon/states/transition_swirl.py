# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface
from pygame.transform import rotate, scale

from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class SwirlTransition(State):
    """The state responsible for the swirl transitions."""

    name: ClassVar[str] = "SwirlTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        image: Surface,
        scale: float = 1.2,
        speed: float = 50.0,
        **kwargs: Any,
    ) -> None:
        """
        Parameters:
            image: The image to be used for the swirl effect.
            scale: The initial scale factor of the image. Defaults to 1.2,
                meaning the image will start at 120% of its original size.
            speed: The rate of rotation in degrees per second. Defaults to 50.
        """
        super().__init__(client=client, **kwargs)
        logger.info("Initializing Swirl transition")
        self.image = image
        self.center_x = self.client.context.screen.get_width() // 2
        self.center_y = self.client.context.screen.get_height() // 2
        self.angle = 0.0
        self.scale = scale
        self.speed = speed

    def update(self, dt: float) -> None:
        self.angle += self.speed * dt
        self.scale += 0.01 * dt
        if self.angle > 360:
            logger.info("Swirl transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        surface.fill((0, 0, 0))
        rotated_image = rotate(self.image, self.angle)
        scaled_image = scale(
            rotated_image,
            (
                int(rotated_image.get_width() * self.scale),
                int(rotated_image.get_height() * self.scale),
            ),
        )
        rect = scaled_image.get_rect(center=(self.center_x, self.center_y))
        surface.blit(scaled_image, rect)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None
