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


class PixelationTransition(State):
    """The state responsible for the pixelation transitions."""

    name: ClassVar[str] = "PixelationTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        duration: float = 1.0,
        scale_factor: float = 10.0,
        **kwargs: Any,
    ) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
            scale_factor: The level of pixelation or blockiness applied
                to the screen, with higher values resulting in a more
                extreme effect.
        """
        super().__init__(client=client, **kwargs)
        logger.info("Initializing Pixelation transition")
        self.duration = duration
        self.scale_factor = scale_factor
        self.start_time = 0.0
        self.elapsed_time = 0.0

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if self.elapsed_time > self.duration:
            logger.info("Pixelation transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        small_screen = scale(
            surface,
            (
                surface.get_width() // self.scale_factor,
                surface.get_height() // self.scale_factor,
            ),
        )
        surface.blit(scale(small_screen, surface.get_size()), (0, 0))

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # prevent other states from getting input
        return None
