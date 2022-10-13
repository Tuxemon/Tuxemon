#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Leif Theden <leif.theden@gmail.com>
# Carlos Ramos <vnmabus@gmail.com>
#
#
# states.FlashTransition
#
from __future__ import annotations

import logging
from typing import Any, Optional

import pygame

from tuxemon import prepare
from tuxemon.platform.events import PlayerInput
from tuxemon.state import State

logger = logging.getLogger(__name__)


class FlashTransition(State):
    """The state responsible for the battle transitions."""

    force_draw = True

    def startup(self, **kwargs: Any) -> None:
        logger.info("Initializing battle transition")
        self.flash_time = 0.2  # Time in seconds between flashes
        self.flash_state = "up"
        self.transition_alpha = 0.0
        self.max_flash_count = 7
        self.flash_count = 0
        self.client.rumble.rumble(-1, length=1.5)

    def resume(self) -> None:
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill((255, 255, 255))

    def update(self, time_delta: float) -> None:
        """
        Update function for state.

        Parameters:
            time_delta: Time since last update in seconds

        """
        logger.info("Battle transition!")

        # self.battle_transition_alpha
        if self.flash_state == "up":
            self.transition_alpha += 255 * (time_delta / self.flash_time)

        elif self.flash_state == "down":
            self.transition_alpha -= 255 * (time_delta / self.flash_time)

        if self.transition_alpha >= 255:
            self.flash_state = "down"
            self.flash_count += 1

        elif self.transition_alpha <= 0:
            self.flash_state = "up"
            self.flash_count += 1

        # If we've hit our max number of flashes, stop the battle
        # transition animation.
        if self.flash_count > self.max_flash_count:
            logger.info(
                "Flashed "
                + str(self.flash_count)
                + " times. Stopping transition.",
            )
            self.client.pop_state()

    def draw(self, surface: pygame.surface.Surface) -> None:
        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(int(self.transition_alpha))
        surface.blit(self.transition_surface, (0, 0))

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        # prevent other states from getting input
        return None
