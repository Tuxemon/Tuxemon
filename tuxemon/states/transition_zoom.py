# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface
from pygame.transform import scale

from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class ZoomOutTransition(State):
    """The state responsible for the zoom out transitions."""

    name: ClassVar[str] = "ZoomOutTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        image: Surface,
        scale: float = 0.1,
        speed: float = 0.5,
        **kwargs: Any,
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
        super().__init__(client=client, **kwargs)
        logger.info("Initializing Zoom Out transition")
        self.image = image
        self.scale = scale
        self.speed = speed  # scale factor per second

    def update(self, dt: float) -> None:
        if self.scale < 1.0:
            self.scale += self.speed * dt
        else:
            self.scale = 1.0

        if self.scale >= 1.0:
            logger.info("Zoom Out transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        scaled_image = scale(
            self.image,
            (
                int(self.image.get_width() * self.scale),
                int(self.image.get_height() * self.scale),
            ),
        )
        rect = scaled_image.get_rect(
            center=(
                self.client.context.screen.get_width() // 2,
                self.client.context.screen.get_height() // 2,
            )
        )
        surface.blit(scaled_image, rect)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None


class ZoomInTransition(State):
    """The state responsible for the zoom in transitions."""

    name: ClassVar[str] = "ZoomInTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        image: Surface,
        scale: float = 1.0,
        speed: float = 0.5,
        **kwargs: Any,
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
        super().__init__(client=client, **kwargs)
        logger.info("Initializing Zoom In transition")
        self.image = image
        self.scale = scale
        self.speed = speed  # scale factor per second

    def update(self, dt: float) -> None:
        if self.scale > 0.1:
            self.scale -= self.speed * dt
        else:
            self.scale = 0.1

        if self.scale <= 0.1:
            logger.info("Zoom In transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        scaled_image = scale(
            self.image,
            (
                int(self.image.get_width() * self.scale),
                int(self.image.get_height() * self.scale),
            ),
        )
        rect = scaled_image.get_rect(
            center=(
                self.client.context.screen.get_width() // 2,
                self.client.context.screen.get_height() // 2,
            )
        )
        surface.blit(scaled_image, rect)

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None
