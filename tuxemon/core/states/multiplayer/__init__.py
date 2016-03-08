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
# Derek Clark <derekjohn.clark@gmail.com>
#
# core.components.states
#
"""This module contains the Headless Server state.
"""
import logging

from core import prepare
from core.states import world

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


class HeadlessServerState(world.WorldState):
    """ The state responsible for the headless server world state.
    """

    def startup(self, **kwargs):
        # Set the native tile size so we know how much to scale
        self.tile_size = prepare.TILE_SIZE

        # Set the status icon size so we know how much to scale
        self.icon_size = prepare.ICON_SIZE

        # Get the screen's resolution
        self.resolution = prepare.SCREEN_SIZE

        # Native resolution is similar to the old gameboy resolution. This is
        # used for scaling.
        self.native_resolution = prepare.NATIVE_RESOLUTION

        # Set the tiles and mapsize variables
        self.tiles = []
        self.map_size = []

        self.global_x = 0
        self.global_y = 0

        self.npcs = []
        self.npcs_off_map = []
