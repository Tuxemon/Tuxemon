# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.surface import Surface

from tuxemon.graphics import ColorLike
from tuxemon.platform.const.graphics import WHITE_COLOR
from tuxemon.rumble.tools import RumbleParams
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class FlashTransition(State):
    """The state responsible for the battle transitions."""

    name: ClassVar[str] = "FlashTransition"
    force_draw = True

    def __init__(
        self,
        client: BaseClient,
        color: ColorLike = WHITE_COLOR,
        flash_time: float = 0.2,
        max_flash_count: int = 7,
        **kwargs: Any,
    ) -> None:
        """
        Parameters:
            color: The color to use for the flash effect. Defaults to white.
            flash_time: The time in seconds between flashes. Defaults to 0.2
                seconds.
            max_flash_count: The maximum number of times the flash effect will
                repeat. Defaults to 7.
        """
        super().__init__(client=client, **kwargs)
        logger.info("Initializing battle transition")
        self.flash_time = flash_time
        self.flash_state = "up"
        self.transition_alpha = 0.0
        self.max_flash_count = max_flash_count
        self.flash_count = 0
        params = RumbleParams(target=-1, length=1.5)
        self.client.rumble_manager.rumble(params)
        self.color = color
        self.transition_surface = Surface(self.client.context.resolution)
        self.transition_surface.fill(self.color)

    def resume(self) -> None:
        self.transition_surface.fill(self.color)

    def update(self, dt: float) -> None:
        logger.info("Battle transition!")

        if self.flash_state == "up":
            self.transition_alpha = min(
                255,
                self.transition_alpha + 255 * (dt / self.flash_time),
            )
        elif self.flash_state == "down":
            self.transition_alpha = max(
                0, self.transition_alpha - 255 * (dt / self.flash_time)
            )

        if self.transition_alpha >= 255:
            self.flash_state = "down"
            self.flash_count += 1
        elif self.transition_alpha <= 0:
            self.flash_state = "up"
            self.flash_count += 1

        if self.flash_count > self.max_flash_count:
            logger.info(
                f"Flashed {self.flash_count} times. Stopping transition."
            )
            self.client.pop_state()

    def draw(self, surface: Surface) -> None:
        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(int(self.transition_alpha))
        surface.blit(self.transition_surface, (0, 0))

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        # prevent other states from getting input
        return None
