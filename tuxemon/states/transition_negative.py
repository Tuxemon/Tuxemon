# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class NegativeTransition(State):
    """The state responsible for the negative transitions."""

    name: ClassVar[str] = "NegativeTransition"
    force_draw = True

    def __init__(
        self, client: BaseClient, duration: float = 1.0, **kwargs: Any
    ) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
        """
        super().__init__(client=client, **kwargs)
        logger.info("Initializing negative transition")
        self.duration = duration
        self.start_time = 0.0
        self.elapsed_time = 0.0

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if self.elapsed_time > self.duration:
            logger.info("Negative colors transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                r, g, b, a = surface.get_at((x, y))
                r = 255 - r
                g = 255 - g
                b = 255 - b
                surface.set_at((x, y), (r, g, b, a))

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # prevent other states from getting input
        return None
