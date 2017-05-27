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
# core.prepare Prepares the game environment.
#
"""This module initializes the display and creates dictionaries of resources.
It contains all the static and dynamic variables used throughout the game such
as display resolution, scale, etc.
"""

import os
import shutil

import pygame as pg

from .components import config
from .platform import get_config_directory, get_data_directory, get_cache_directory


# Get the tuxemon base directory
BASEDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")) + os.sep
if "library.zip" in BASEDIR:
    BASEDIR = os.path.abspath(os.path.join(BASEDIR, "..")) + os.sep

# Set up our config directory
CONFIG_PATH = get_config_directory()
try:
    os.makedirs(CONFIG_PATH)
except OSError:
    if not os.path.isdir(CONFIG_PATH):
        raise

DATA_PATH = get_data_directory()
try:
    os.makedirs(DATA_PATH)
except OSError:
    if not os.path.isdir(DATA_PATH):
        raise

CACHE_PATH = get_cache_directory()
try:
    os.makedirs(CACHE_PATH)
except OSError:
    if not os.path.isdir(CACHE_PATH):
        raise

# Create a copy of our default config if one does not exist in the home dir.
CONFIG_FILE_PATH = CONFIG_PATH + "tuxemon.cfg"
if not os.path.isfile(CONFIG_FILE_PATH):
    try:
        shutil.copyfile(BASEDIR + "tuxemon.cfg", CONFIG_FILE_PATH)
    except OSError:
        raise

# Set up our custom campaign data directory.
USER_DATA_PATH = DATA_PATH

# Read the "tuxemon.cfg" configuration file
CONFIG = config.Config(CONFIG_FILE_PATH)
HEADLESSCONFIG = config.HeadlessConfig(CONFIG_FILE_PATH)

# Set up the screen size and caption
SCREEN_SIZE = CONFIG.resolution
ORIGINAL_CAPTION = "Tuxemon"

# Set the native tile size so we know how much to scale our maps
TILE_SIZE = [16, 16]  # 1 tile = 16 pixels

# Set the status icon size so we know how much to scale our menu icons
ICON_SIZE = [7, 7]

# Set the healthbar _color
HP_COLOR = (112, 248, 168)

# Set the XP bar _color
XP_COLOR = (248, 245, 71)

# Native resolution is similar to the old gameboy resolution. This is
# used for scaling.
NATIVE_RESOLUTION = [240, 160]

# If scaling is enabled, scale the tiles based on the resolution
if CONFIG.scaling == "1":
    SCALE = int((SCREEN_SIZE[0] / NATIVE_RESOLUTION[0]))
    TILE_SIZE[0] *= SCALE
    TILE_SIZE[1] *= SCALE
else:
    SCALE = 1

# Set up the saves directory
try:
    os.makedirs(DATA_PATH + "saves/")
except OSError:
    if not os.path.isdir(DATA_PATH + "saves/"):
        raise

SAVE_PATH = DATA_PATH + "saves/slot"

# Initialization of PyGame dependent systems.
def init():
    """The init function is used to initialize all PyGame dependent
    systems. This is primarily implemented to allow sphinx-apidoc
    to autogenerate documentation without initializing a PyGame
    window.

    :param None:

    :rtype: None
    :returns: None

    """

    # These variables will persist throughout the module so they
    # can be called externally. E.g. "prepare.SCREEN", etc.
    global SCREEN
    global SCREEN_RECT
    global JOYSTICKS
    global player1
    global FONTS
    global MUSIC
    global SFX
    global GFX

    # initialize any platform-specific workarounds before pygame
    from core import platform
    platform.init()

    from .platform import android

    # Initialize PyGame and our screen surface.
    pg.init()
    pg.display.set_caption(ORIGINAL_CAPTION)
    SCREEN = pg.display.set_mode(SCREEN_SIZE, CONFIG.fullscreen, 32)
    SCREEN_RECT = SCREEN.get_rect()

    # Disable the mouse cursor visibility
    pg.mouse.set_visible(False)

    # Set up any gamepads that we detect
    # The following event types will be generated by the joysticks:
    # JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
    pg.joystick.init()
    JOYSTICKS = [pg.joystick.Joystick(x)
                 for x in range(pg.joystick.get_count())]

    # Initialize the individual joysticks themselves.
    for joystick in JOYSTICKS:
        joystick.init()

    # Map the appropriate android keys if we're on android
    if android:
        android.init()
        android.map_key(android.KEYCODE_MENU, pg.K_ESCAPE)

    # Create an instance of the player and list of NPCs
    from .components import player
    player1 = player.Player()

    # Scale the sprite and its animations
    for key, animation in player1.sprite.items():
        animation.scale(
                tuple(i * SCALE for i in animation.getMaxSize()))

    for key, image in player1.standing.items():
        player1.standing[key] = pg.transform.scale(
                image, (image.get_width() * SCALE,
                        image.get_height() * SCALE))

    # Set the player's width and height based on the size of our scaled
    # sprite.
    player1.playerWidth, player1.playerHeight = \
        player1.standing["front"].get_size()
    player1.playerWidth = TILE_SIZE[0]
    player1.playerHeight = TILE_SIZE[1]
    player1.tile_size = TILE_SIZE

    # Put the player right in the middle of our screen.
    player1.position = [
        (SCREEN_SIZE[0] / 2) - (player1.playerWidth / 2),
        (SCREEN_SIZE[1] / 2) - (player1.playerHeight / 2)]

    # Set the player's collision rectangle
    player1.rect = pg.Rect(
            player1.position[0],
            player1.position[1],
            TILE_SIZE[0],
            TILE_SIZE[1])

    # Set the walking and running pixels per second based on the scale
    player1.walkrate *= SCALE
    player1.runrate *= SCALE
