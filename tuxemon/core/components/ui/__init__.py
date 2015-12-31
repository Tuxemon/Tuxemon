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
# core.components.ui User interface handling module.
#
#

import logging
import pygame
import operator

from core.components import pyganim
from core.components import plugin
from core import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("components.ui successfully imported")


class UserInterface(object):
    """A basic user interface object.

    :param image: Path to the image to load or surface.
    :param position: The [x, y] position to draw the UI element.
    :param screen: The pygame surface to draw the element on.
    :param scale: Whether or not to scale the surface based on game's scale.

    :type image: String or pygame.Surface
    :type position: List
    :type screen: pygame.Surface
    :type scale: Boolean

    """
    def __init__(self, images, position, screen, scale=True,
                 animation_speed=0.2, animation_loop=False):

        # Check to see what kind of image(s) are being loaded.
        images_type = type(images).__name__

        # Handle loading a single image, multiple images, or surfaces
        if images_type == 'str' or images_type == 'unicode':
            if prepare.BASEDIR not in images:
                images = prepare.BASEDIR + images
            surface = pygame.image.load(images).convert_alpha()
            self.original_width = surface.get_width()
            self.original_height = surface.get_height()
            if scale:
                surface = self.scale_surface(surface)
            self.images = [(surface, animation_speed)]

        elif images_type == 'list' or images_type == 'tuple':
            self.images = []
            for item in images:
                item_type = type(item).__name__
                if item_type == 'str' or item_type == 'unicode':
                    surface = pygame.image.load(item).convert_alpha()
                    self.original_width = surface.get_width()
                    self.original_height = surface.get_height()
                    if scale:
                        surface = self.scale_surface(surface)
                else:
                    self.original_width = surface.get_width()
                    self.original_height = surface.get_height()
                    if scale:
                        surface = self.scale_surface(surface)
                    else:
                        surface = item
                self.images.append((surface, animation_speed))

        else:
            self.original_width = images.get_width()
            self.original_height = images.get_height()
            if scale:
                surface = self.scale_surface(images)
            else:
                surface = images
            self.images = [(surface, animation_speed)]

        # Create a pyganimation object using our loaded images.
        self.animation = pyganim.PygAnimation(self.images, loop=animation_loop)
        self.animation.play()
        self.animation.pause()

        self.position = position
        self.last_position = position
        self.screen = screen
        self.visible = True
        self.state = ""

        self.width = self.images[0][0].get_width()
        self.height = self.images[0][0].get_height()
        self.moving = False
        self.move_destination = (0, 0)
        self.move_delta = [0, 0]
        self.move_duration = 0.
        self.move_time = 0.
        self.fading = False
        self.fade_duration = 0.
        self.shaking = False


    def scale_surface(self, surface):
        """Scales the interface based on the game's scale.

        :param: None
        :type: None

        """
        width = surface.get_width()
        height = surface.get_height()
        scaled_surface = pygame.transform.scale(surface,
                                                (width * prepare.SCALE,
                                                height * prepare.SCALE))

        return scaled_surface


    def update(self, dt):
        """Updates the object based on its current state.

        :param dt: Amount of time passed in seconds since the last frame.
        :type dt: Float

        """
        if self.moving:
            self.move_time += dt
            dest = self.move_destination
            dur = self.move_duration
            mdt = self.move_delta
            mt = self.move_time
            if mt > dur:
                self.position = dest
                self.moving = False
                if self.state == "moving" or self.state == "back":
                    self.state = ""
                elif self.state == "forward":
                    self.move(self.last_position, self.move_duration)
                    self.state == "back"
            else:
                if type(self.position) is tuple:
                    self.position = list(self.position)

                self.position[0] -= (mdt[0] * dt) / dur
                self.position[1] -= (mdt[1] * dt) / dur


    def draw(self):
        """Draws the UI element to the screen.

        :param: None
        :type: None

        """
        if self.visible:
            if self.shaking:
                # Do shaking stuff
                pos = self.position
            else:
                pos = self.position
            self.animation.blit(self.screen, pos)


    def play(self):
        self.animation.play()


    def pause(self):
        self.animation.pause()


    def stop(self):
        self.animation.stop()


    def shake(self, intensity, direction="random"):
        """Shakes the object a given severity.

        :param intensity: How much the object will shake.
        :param direction: Direction to shake in degrees, defaults to "random".

        :type intensity: Int
        :type direction: Int or String

        """
        pass


    def fade_in(self, duration=1.):
        """Fades the object in.

        :param duration: Fade the object in over n seconds, defaults to 1.
        :type duration: Float

        """
        if not self.state == "fading_in":
            self.state = "fading_in"
            self.fading = "in"
            self.fade_duration = duration


    def fade_out(self, duration=1.):
        """Fades the object out.

        :param duration: Fade the object out over n seconds, defaults to 1.
        :type duration: Float

        """
        if not self.state == "fading_out":
            self.state = "fading_out"
            self.fading = "out"
            self.fade_duration = duration


    def move(self, destination, duration=1.):
        """Moves the object to position over n seconds.

        :param destination: The (x, y) screen destination position to move to.
        :param duration: Moves the object over n seconds, defaults to 1.

        :type destination: Tuple
        :type duration: Float

        """

        if not self.state == "moving":
            self.state = "moving"
            self.moving = True
            self.last_position = list(self.position)
            self.move_destination = destination
            self.move_time = 0.
            self.move_delta.append(self.position[1] - destination[1])
            self.move_delta = list(map(operator.sub, self.position, destination))
            self.move_duration = float(duration)


    def shake_once(self, destination, duration=0.3):
        """Moves the object to a position and then back to its original position.
        """

        if not self.state == "forward" or not self.state == "back":
            self.move(destination, duration)
            self.state = "forward"


    def scale(self, width_height):
        self.animation.scale(width_height)


import core.components.ui.bar
