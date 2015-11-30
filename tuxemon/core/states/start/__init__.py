#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# William Edwards <shadowapex@gmail.com>
#
#
# core.states.start Handles the splash screen and start menu.
#
#

import logging
import pygame

from core import prepare
from core import state


# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.start successfully imported")


class START(state.State):
    """The module responsible for the splash screen and start menu.

    :param game: The scene manager object that contains all the game's variables.
    :type game: core.tools.Control

    """

    def __init__(self, game):
        # Initiate our common state properties.
        state.State.__init__(self)

        # The scene to load next when this scene has been completed.
        self.next = "WORLD"

        # Provide an instance of the scene manager to this scene.
        self.game = game            # The scene manger object
        self.state = "Splash"       # Can be Splash or Menu
        self.fade = "in"            # Can be "in", "out", "waiting", or None

        # Create a surface to be used for transitions
        self.transition = {}
        self.transition['surface'] = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition['surface'].fill((0,0,0))
        self.transition['surface'].set_alpha(255)
        self.transition['alpha'] = 255
        self.transition['time'] = 2     # 5 second transition time
        self.wait_time = 0              # Current time we've waited between splash and start of game

        # Set up the splash screen logos
        self.splash_pygame = {}
        self.splash_pygame['path'] = prepare.BASEDIR + "resources/gfx/ui/intro/pygame_logo.png"
        self.splash_pygame['surface'] = pygame.image.load(self.splash_pygame['path'])
        self.splash_pygame['surface'] = pygame.transform.scale(self.splash_pygame['surface'],
                                                           (self.splash_pygame['surface'].get_width() * prepare.SCALE,
                                                            self.splash_pygame['surface'].get_height() * prepare.SCALE
                                                            ))

        splash_border = prepare.SCREEN_SIZE[0] / 20     # The space between the edge of the screen
        self.splash_pygame['position'] = (splash_border,
                                          prepare.SCREEN_SIZE[1] - splash_border - self.splash_pygame['surface'].get_height())

        self.splash_cc = {}
        self.splash_cc['path'] = prepare.BASEDIR + "resources/gfx/ui/intro/creative_commons.png"
        self.splash_cc['surface'] = pygame.image.load(self.splash_cc['path'])
        self.splash_cc['surface'] = pygame.transform.scale(self.splash_cc['surface'],
                                                           (self.splash_cc['surface'].get_width() * prepare.SCALE,
                                                            self.splash_cc['surface'].get_height() * prepare.SCALE
                                                            ))
        self.splash_cc['position'] = (prepare.SCREEN_SIZE[0] - splash_border - self.splash_cc['surface'].get_width(),
                                      prepare.SCREEN_SIZE[1] - splash_border - self.splash_cc['surface'].get_height())


    def startup(self, current_time, persistant):
        """Perform startup tasks when we switch to this scene.

        :param current_time: Current time passed.
        :param persistant: Keep a dictionary of optional persistant variables.

        :type current_time: Integer
        :type persistant: Dictionary

        :rtype: None
        :returns: None


        **Examples:**

        >>> current_time
        2895
        >>> persistant
        {}

        """

        self.persist = persistant
        self.start_time = current_time

        self.state = "Splash"       # Can be Splash or Menu
        self.fade = "in"            # Can be "in", "out", "waiting", or None


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

        self.draw()


    def get_event(self, event):
        """Processes events that were passed from the main event loop.
        Must be overridden in children.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """

        # Skip the splash screen if a key is pressed.
        if event.type == pygame.KEYDOWN and self.state == "Splash":
            self.fade = None
            self.state = None
            self.done = True


    def draw(self):
        """Draws the start screen to the screen.

        :param None:
        :type None:

        :rtype: None
        :returns: None

        """

        self.game.screen.fill((15, 15, 15))

        # Skip the splash screen if it is disabled in the game configuration
        if prepare.CONFIG.splash != "1":
                self.fade = None
                self.state = None
                # Start the game after splash
                self.done = True

        if self.state == "Splash":
            self.game.screen.blit(self.splash_pygame['surface'], self.splash_pygame['position'])
            self.game.screen.blit(self.splash_cc['surface'], self.splash_cc['position'])

        if self.fade == "in":

            self.transition['alpha'] -= (255 * ((self.game.time_passed_seconds)/self.transition['time']))
            self.transition['surface'].set_alpha(self.transition['alpha'])

            self.game.screen.blit(self.transition['surface'], (0,0))

            if self.transition['alpha'] < 0:
                self.fade = "waiting"

        elif self.fade == "out":

            self.transition['alpha'] += (255 * ((self.game.time_passed_seconds)/self.transition['time']))
            self.transition['surface'].set_alpha(self.transition['alpha'])

            self.game.screen.blit(self.transition['surface'], (0,0))

            if self.transition['alpha'] > 255:
                self.fade = None
                self.state = None
                # Start the game after splash
                self.done = True

        elif self.fade == "waiting":
            self.wait_time += self.game.time_passed_seconds

            if self.wait_time > self.transition['time']:
                self.fade = "out"

