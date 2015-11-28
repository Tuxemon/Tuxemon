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
# core.tools Contains various tools such as scene manager and states.
#
"""This module contains the fundamental Control class and a prototype class
for States.  Also contained here are resource loading functions.
"""

import logging
import os
import pprint

import pygame as pg
from .components import ai
from .components import cli
from .components import db
from .components import item
from .components import map as maps
from .components import monster
from .components import networking
from .components import player
from .components import pyganim
from .components import rumble

# Import the android module and android specific components. If we can't import, set to None - this
# lets us test it, and check to see if we want android-specific behavior.
try:
    import android
except ImportError:
    android = None

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

# Create a pretty printer for debugging
pp = pprint.PrettyPrinter(indent=4)


import time
class HeadlessControl():
    """Control class for headless server. Contains the game loop, and contains
    the event_loop which passes events to States as needed. Logic for flipping
    states is also found here.

    :param: None
    :rtype: None
    :returns: None

    """
    def __init__(self):
        self.done = False

        self.clock = time.clock()
        self.fps = 60.0
        self.current_time = 0.0

        self.server = networking.TuxemonServer(self)
#         self.server_thread = threading.Thread(target=self.server)
#         self.server_thread.start()
        self.server.server.listen()

        #Set up our game's configuration from the prepare module.
        from core import prepare
        self.imports = {
                "prepare": prepare,
                "ai": ai,
                "rumble": rumble,
                "db": db,
                "monster": monster,
                "player": player,
                "item": item,
                "map": maps,
                "pyganim": pyganim
                }
        self.config = prepare.HEADLESSCONFIG

        # Set up the command line. This provides a full python shell for
        # troubleshooting. You can view and manipulate any variables in
        # the game.
        self.exit = False   # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

    def setup_states(self, state_dict, start_state):
        """Given a dictionary of States and a State to start in,
        builds the self.state_dict.

        :param state_dict: A dictionary of core.tools.State objects.
        :param start_state: A string of the starting state. E.g. "START"

        :type state_dict: Dictionary
        :type start_state: String

        :rtype: None
        :returns: None

        **Examples:**

        >>> state_dict
        {'COMBAT': <core.states.combat.Combat object at 0x7f681d736590>,
         'START': <core.states.start.StartScreen object at 0x7f68230f5150>,
         'WORLD': <core.states.world.World object at 0x7f68230f54d0>}
        >>> start_state
        "START"

        """

        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]


    def main(self):
        """Initiates the main game loop. Since we are using Asteria networking
        to handle network events, we pass this core.tools.Control instance to
        networking which in turn executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.

        :param None:

        :rtype: None
        :returns: None

        """
        while not self.exit:
            self.main_loop()


    def main_loop(self):
        """Main loop for entire game. This method gets execute every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        :param None:

        :rtype: None
        :returns: None

        """
        # Get the amount of time that has passed since the last frame.
#         self.time_passed_seconds = time.clock() - self.clock

#         self.server.update()

        if self.exit:
            self.done = True

#         self.clock = time.clock()


### Resource loading functions.
def load_all_gfx(directory, colorkey=(255,0,255), accept=(".png",".jpg",".bmp")):
    """Load all graphics with extensions in the accept argument.  If alpha
    transparency is found in the image the image will be converted using
    convert_alpha().  If no alpha transparency is detected image will be
    converted using convert() and colorkey will be set to colorkey."""
    graphics = {}

    for root, directories, filenames in os.walk(directory):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            if ext.lower() in accept:
                img = pg.image.load(os.path.join(root, filename))
                if img.get_alpha():
                    img = img.convert_alpha()
                else:
                    img = img.convert()
                    img.set_colorkey(colorkey)
                graphics[name] = img

    return graphics


def load_all_music(directory, accept=(".ogg", ".mdi")):
    """Create a dictionary of paths to music files in given directory
    if their extensions are in accept."""
    songs = {}
    for root, directories, filenames in os.walk(directory):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            if ext.lower() in accept:
                song = os.path.join(root, filename)
                songs[name] = song
    return songs


def load_all_fonts(directory, accept=(".ttf",)):
    """Create a dictionary of paths to font files in given directory
    if their extensions are in accept."""
    return load_all_music(directory, accept)


def load_all_movies(directory, accept=(".mpg",)):
    """Create a dictionary of paths to movie files in given directory
    if their extensions are in accept."""
    return load_all_music(directory, accept)


def load_all_sfx(directory, accept=(".ogg", ".mdi")):
    """Load all sfx of extensions found in accept.  Unfortunately it is
    common to need to set sfx volume on a one-by-one basis.  This must be done
    manually if necessary in the setup module."""
    effects = {}
    for root, directories, filenames in os.walk(directory):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            if ext.lower() in accept:
                effects[name] = pg.mixer.Sound(os.path.join(root, filename))

    return effects


def load_all_maps(directory, accept=(".tmx")):
    pass


def strip_from_sheet(sheet, start, size, columns, rows=1):
    """Strips individual frames from a sprite sheet given a start location,
    sprite size, and number of columns and rows."""
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pg.Rect(location, size)))
    return frames


def strip_coords_from_sheet(sheet, coords, size):
    """Strip specific coordinates from a sprite sheet."""
    frames = []
    for coord in coords:
        location = (coord[0]*size[0], coord[1]*size[1])
        frames.append(sheet.subsurface(pg.Rect(location, size)))
    return frames


def get_cell_coordinates(rect, point, size):
    """Find the cell of size, within rect, that point occupies."""
    cell = [None, None]
    point = (point[0]-rect.x, point[1]-rect.y)
    cell[0] = (point[0]//size[0])*size[0]
    cell[1] = (point[1]//size[1])*size[1]
    return tuple(cell)


def cursor_from_image(image):
    """Take a valid image and create a mouse cursor."""
    colors = {(0,0,0,255) : "X",
              (255,255,255,255) : "."}
    rect = image.get_rect()
    icon_string = []
    for j in range(rect.height):
        this_row = []
        for i in range(rect.width):
            pixel = tuple(image.get_at((i,j)))
            this_row.append(colors.get(pixel, " "))
        icon_string.append("".join(this_row))
    return icon_string


def explore(rootdir):
    """
    Creates a nested dictionary that represents the folder structure of rootdir
    """
    dir = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir

    for key, value in dir.items():
        for k, v in value.items():
            return v

