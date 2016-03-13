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
from core import tools

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class SplashState(state.State):
    """ The state responsible for the splash screen
    """
    default_duration = 3

    def fade_out(self):
        self.game.push_state("FadeOutTransition", caller=self)

    def startup(self, **kwargs):
        # this task will skip the splash screen after some time
        self.task(self.fade_out, self.default_duration)

        width, height = prepare.SCREEN_SIZE
        splash_border = prepare.SCREEN_SIZE[0] / 20     # The space between the edge of the screen

        # Set up the splash screen logos
        logo = self.load_sprite("gfx/ui/intro/pygame_logo.png")
        logo.rect.topleft = splash_border, height - splash_border - logo.rect.height

        # Set up the splash screen logos
        cc = self.load_sprite("gfx/ui/intro/creative_commons.png")
        cc.rect.topleft = width - splash_border - cc.rect.width, height - splash_border - cc.rect.height

        self.ding = tools.load_sound("sounds/ding.wav")
        self.ding.play()

    def process_event(self, event):
        """Processes events that were passed from the main event loop.

        :param event: A pygame key event from pygame.event.get()

        :type event: PyGame Event

        :rtype: None
        :returns: None

        """
        # Skip the splash screen if a key is pressed.
        if event.type == pygame.KEYDOWN:
            self.fade_out()

    def draw(self, surface):
        """Draws the start screen to the screen.

        :param surface:
        :param Surface: Surface to draw to

        :type Surface: pygame.Surface

        :rtype: None
        :returns: None

        """
        surface.fill((15, 15, 15))
        self.sprites.draw(surface)
