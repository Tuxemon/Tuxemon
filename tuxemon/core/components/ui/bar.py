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
# core.components.ui.bar UI bar handling module.
#
#

import logging
import pygame

from core.components.ui import UserInterface
from ... import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class Bar(UserInterface):
    """A user interface bar used for health bars, etc.

    :param size: The [x, y] size of the bar.
    :param position: The [x, y] position to draw the UI element.
    :param _color: The (r,g,b) _color value of the bar.
    :param value: Percentage of the bar filled.

    :type image: List
    :type position: List
    :type screen: pygame.Surface
    :type color: Tuple
    :type value: Float

    """
    def __init__(self, position, animation_speed=0.2):
        color = 0, 255, 0
        self.surface = pygame.Surface((100, 3))
        self.surface.fill(color)
        UserInterface.__init__(self, self.surface, position)
        self.width_original = self.surface.get_width()
        self.height_original = self.surface.get_height()
        self.color = color
        self.visible = True
        self.value = 1

    def draw(self, surface):
        # Don't draw the surface if our width is less than 1 pixel.
        if int(self.rect.width * (self.value * 0.01)) <= 0:
            return

        if self.visible and self.value > 0:
            self.animation.blit(surface, self.rect)

    def __setattr__(self, key, value):
        """Detects changes to the bar class' attributes.

        :param key: The attribute being changed.
        :param value: The value the attribute is being changed to.

        :type key: String
        :type value: Any

        """
        #print("Changing", key, "to", value)
        # If our value changes, scale the bar based on our value.
        if key == "value":
            if value:
                width = int(self.rect.width * (value * 0.01))
                #print("Scaling bar to size: %i * (%f * 0.01) = %i" % (self.width, value, width))
                height = self.rect.height
                if width <= 0:
                    width = 1
                self.animation.scale((width, height))

        self.__dict__[key] = value


