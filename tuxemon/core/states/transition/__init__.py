#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2015, William Edwards <shadowapex@gmail.com>,
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
# William Edwards <shadowapex@gmail.com>
#
#
# core.states.transition Handles the battle transition.
#
#

import logging
import pygame

from core import prepare
from core import state


# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.transition successfully imported")


class TRANSITION(state.State):
    """ The state responsible for the battle transitions.
    """

    def startup(self, params=None):
        self.screen = params["screen"]
        self.combat_params = params

        self.original_surface = self.screen.copy()
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill((255, 255, 255))
        self.flash_time = 0.2  # Time in seconds between flashes
        self.battle_flash_state = "up"
        self.battle_transition_alpha = 0

        self.max_battle_flash_count = 7
        self.battle_flash_count = 0

        logger.info("Initializing battle transition")
        self.game.rumble.rumble(-1, length=1.5)

    def update(self, screen, keys, current_time, time_delta):
        """Update function for state.

        :param surface: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.

        :type surface: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer

        :rtype: None
        :returns: None

        **Examples:**

        >>> surface
        <Surface(1280x720x32 SW)>
        >>> keys
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ...
        >>> current_time
        435

        """
        logger.info("Battle transition!")

        # self.battle_transition_alpha
        if self.battle_flash_state == "up":
            self.battle_transition_alpha += (
                255 * ((time_delta) / self.flash_time))

        elif self.battle_flash_state == "down":
            self.battle_transition_alpha -= (
                255 * ((time_delta) / self.flash_time))

        if self.battle_transition_alpha >= 255:
            self.battle_flash_state = "down"
            self.battle_flash_count += 1

        elif self.battle_transition_alpha <= 0:
            self.battle_flash_state = "up"
            self.battle_flash_count += 1

        # If we've hit our max number of flashes, stop the battle
        # transition animation.
        if self.battle_flash_count > self.max_battle_flash_count:
            logger.info("Flashed " + str(self.battle_flash_count) +
                " times. Stopping transition.")
            self.game.pop_state()
            self.game.push_state("COMBAT", params=self.combat_params)

        self.draw()


    def get_event(self, event):
        """Processes events that were passed from the main event loop.
        Must be overridden in children.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        pass


    def draw(self):
        """Draws the start screen to the screen.

        :param None:
        :type None:

        :rtype: None
        :returns: None

        """
        # Blit the original surface to the screen.
        self.game.screen.blit(self.original_surface, (0, 0))

        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(self.battle_transition_alpha)
        self.screen.blit(self.transition_surface, (0, 0))


