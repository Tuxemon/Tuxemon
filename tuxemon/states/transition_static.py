# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class StaticTransition(State):
    """The state responsible for the static transition."""

    name: ClassVar[str] = "StaticTransition"
    force_draw = True

    def __init__(
        self, client: BaseClient, duration: float = 1.0, **kwargs: Any
    ) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
        """
        super().__init__(client=client, **kwargs)
        logger.info("Initializing Static transition")
        self.duration = duration
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.screenshot: Surface | None = None

    def resume(self) -> None:
        self.screenshot = Surface.copy(self.client.context.screen)

    def update(self, dt: float) -> None:
        self.elapsed_time += dt
        if self.elapsed_time > self.duration:
            logger.info("Static transition finished.")
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        surface.fill((0, 0, 0))
        for _ in range(5000):
            x = random.randint(0, surface.get_width())
            y = random.randint(0, surface.get_height())
            surface.set_at(
                (x, y),
                (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                ),
            )

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        return None
