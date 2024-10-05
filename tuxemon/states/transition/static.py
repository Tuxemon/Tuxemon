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


class StaticTransition(State):
    """The state responsible for the static transition."""

    force_draw = True

    def __init__(self, duration: float = 1.0) -> None:
        """
        Parameters:
            duration: The time in seconds. Defaults to 1.0 seconds.
        """
        super().__init__()
        logger.info("Initializing Static transition")
        self.duration = duration
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.screenshot: Optional[pygame.Surface] = None

    def resume(self) -> None:
        self.screenshot = pygame.Surface.copy(prepare.SCREEN)

    def update(self, time_delta: float) -> None:
        self.elapsed_time += time_delta
        if self.elapsed_time > self.duration:
            logger.info("Static transition finished.")
            self.client.pop_state()

    def draw(self, surface: pygame.surface.Surface) -> None:
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

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
