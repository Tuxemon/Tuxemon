# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module initializes the display and creates dictionaries of resources.
It contains all the static and dynamic variables used throughout the game such
as display resolution, scale, etc.
"""
from __future__ import annotations

import logging
import os.path
import re
from typing import TYPE_CHECKING

from tuxemon import config
from tuxemon.constants import paths

if TYPE_CHECKING:
    import pygame as pg

    SCREEN: pg.surface.Surface
    SCREEN_RECT: pg.rect.Rect
    JOYSTICKS: list[pg.joystick.Joystick]

logger = logging.getLogger(__name__)

# TODO: refact this out when other platforms supported (such as headless)
PLATFORM = "pygame"

# list of regular expressions to blacklist devices
joystick_blacklist = [
    re.compile(r"Microsoft.*Transceiver.*"),
    re.compile(r".*Synaptics.*", re.I),
    re.compile(r"Wacom*.", re.I),
]

# Create game dir if missing
if not os.path.isdir(paths.USER_STORAGE_DIR):
    os.makedirs(paths.USER_STORAGE_DIR)

# Create game data dir if missing
if not os.path.isdir(paths.USER_GAME_DATA_DIR):
    os.makedirs(paths.USER_GAME_DATA_DIR)

# Create game savegame dir if missing
if not os.path.isdir(paths.USER_GAME_SAVE_DIR):
    os.makedirs(paths.USER_GAME_SAVE_DIR)

# Generate default config
config.generate_default_config()

# Read "tuxemon.cfg" config from disk, update and write back
CONFIG = config.TuxemonConfig(paths.USER_CONFIG_PATH)

# Starting map
STARTING_MAP = "debug.tmx"

with open(paths.USER_CONFIG_PATH, "w") as fp:
    CONFIG.cfg.write(fp)

# Set up the screen size and caption
SCREEN_SIZE = CONFIG.resolution

# Set the native tile size so we know how much to scale our maps
# 1 tile = 16 pixels
TILE_SIZE = (16, 16)

# Set the status icon size so we know how much to scale our menu icons
ICON_SIZE = [7, 7]

# Set the healthbar _color
HP_COLOR_FG = (10, 240, 25)  # dark saturated green
HP_COLOR_BG = (245, 10, 25)  # dark saturated red

# Set the XP bar _color
XP_COLOR_FG = (31, 239, 255)  # light washed cyan
XP_COLOR_BG = None  # none for the moment

# Colors
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
RED_COLOR = (255, 0, 0)
GREEN_COLOR = (0, 255, 0)
FUCHSIA_COLOR = (255, 0, 255)
SEA_BLUE_COLOR = (0, 105, 148)
DARKGRAY_COLOR = (169, 169, 169)
DIMGRAY_COLOR = (105, 105, 105)
# Default colors
TRANSPARENT_COLOR = (255, 255, 255, 0)
BACKGROUND_COLOR = (248, 248, 248)  # Guyabano
FONT_COLOR = BLACK_COLOR
FONT_SHADOW_COLOR = (192, 192, 192)  # silver
SCROLLBAR_COLOR = (237, 246, 248)  # light turquoise
SCROLLBAR_SLIDER_COLOR = (197, 232, 234)  # darker turquoise

if CONFIG.large_gui:
    FONT_SIZE_SMALLER = 4
    FONT_SIZE_SMALL = 5
    FONT_SIZE = 6
    FONT_SIZE_BIG = 7
    FONT_SIZE_BIGGER = 8
else:
    FONT_SIZE_SMALLER = 3
    FONT_SIZE_SMALL = 4
    FONT_SIZE = 5
    FONT_SIZE_BIG = 6
    FONT_SIZE_BIGGER = 7

# Native resolution is similar to the old gameboy resolution. This is
# used for scaling.
NATIVE_RESOLUTION = [240, 160]


# Players
PLAYER_NPC = CONFIG.player_npc
PLAYER_NAME_LIMIT: int = 15  # The character limit for a player name.
PARTY_LIMIT: int = 6  # The maximum number of tuxemon this npc can hold

# PC
KENNEL: str = "Kennel"
LOCKER: str = "Locker"
MAX_KENNEL: int = 30  # nr max of pc monsters
MAX_LOCKER: int = 30  # nr max of pc items

# Items
INFINITE_ITEMS: int = -1
MAX_TYPES_BAG: int = 99  # eg 5 capture devices, 1 type and 5 items

# Monsters
MAX_LEVEL: int = 999
MAX_MOVES: int = 4
MISSING_IMAGE: str = "gfx/sprites/battle/missing.png"
MIN_CATCH_RATE: int = 0
MAX_CATCH_RATE: int = 255
MIN_CATCH_RESISTANCE: float = 0.0
MAX_CATCH_RESISTANCE: float = 2.0
# set multiplier stats (multiplier: level + coefficient)
COEFF_STATS: int = 7
# set experience required for levelling up
# (level + level_ofs) ** coefficient) - level_ofs default 0
COEFF_EXP: int = 3

# Capture
TOTAL_SHAKES: int = 4
MAX_SHAKE_RATE: int = 65536
SHAKE_CONSTANT: int = 524325

# Techniques
MIN_RECHARGE: int = 0
MAX_RECHARGE: int = 5
MIN_POTENCY: float = 0.0
MAX_POTENCY: float = 1.0
MIN_ACCURACY: float = 0.0
MAX_ACCURACY: float = 1.0
MIN_POWER: float = 0.0
MAX_POWER: float = 3.0
MIN_HEALING_POWER: int = 0
MAX_HEALING_POWER: int = 10

# Combat
# This is the coefficient that can be found in formula.py and
# it calculates the user strength
# eg: user_strength = user.melee * (COEFF_DAMAGE + user.level)
COEFF_DAMAGE: int = 7
# Min and max multiplier are the multiplier upper/lower bounds
MIN_MULTIPLIER: float = 0.25
MAX_MULTIPLIER: float = 4.0
# MULT_MAP associates the multiplier to a specific text
MULT_MAP = {
    4: "attack_very_effective",
    2: "attack_effective",
    0.5: "attack_resisted",
    0.25: "attack_weak",
}
# This is the time, in seconds, that the text takes to display.
LETTER_TIME: float = 0.02
# This is the time, in seconds, that the animation takes to finish.
ACTION_TIME: float = 2.0

# Fonts
FONT_BASIC: str = "PressStart2P.ttf"
FONT_CHINESE: str = "SourceHanSerifCN-Bold.otf"
FONT_JAPANESE: str = "SourceHanSerifJP-Bold.otf"

# If scaling is enabled, scale the tiles based on the resolution
if CONFIG.large_gui:
    SCALE = 2
    TILE_SIZE = (TILE_SIZE[0] * SCALE, TILE_SIZE[1] * SCALE)
elif CONFIG.scaling:
    SCALE = int(SCREEN_SIZE[0] / NATIVE_RESOLUTION[0])
    TILE_SIZE = (TILE_SIZE[0] * SCALE, TILE_SIZE[1] * SCALE)
else:
    SCALE = 1

# Reference user save dir
SAVE_PATH = os.path.join(paths.USER_GAME_SAVE_DIR, "slot")
SAVE_METHOD = "JSON"
# SAVE_METHOD = "CBOR"

DEV_TOOLS = CONFIG.dev_tools


def pygame_init() -> None:
    """Eventually refactor out of prepare."""
    global JOYSTICKS
    global FONTS
    global MUSIC
    global SFX
    global GFX
    global SCREEN
    global SCREEN_RECT

    import pygame as pg

    # Configure databases and locale
    from tuxemon.locale import T

    T.collect_languages(CONFIG.recompile_translations)
    from tuxemon.db import db

    db.load()

    logger.debug("pygame init")
    pg.init()
    pg.display.set_caption(CONFIG.window_caption)

    from tuxemon import platform

    if platform.android:
        fullscreen = pg.FULLSCREEN
    else:
        fullscreen = pg.FULLSCREEN if CONFIG.fullscreen else 0
    flags = pg.HWSURFACE | pg.DOUBLEBUF | fullscreen

    SCREEN = pg.display.set_mode(SCREEN_SIZE, flags)
    SCREEN_RECT = SCREEN.get_rect()

    # Disable the mouse cursor visibility
    pg.mouse.set_visible(not CONFIG.hide_mouse)

    # Set up any gamepads that we detect
    # The following event types will be generated by the joysticks:
    # JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
    JOYSTICKS = list()
    pg.joystick.init()
    devices = [pg.joystick.Joystick(x) for x in range(pg.joystick.get_count())]

    # Initialize the individual joysticks themselves.
    for joystick in devices:
        name = joystick.get_name()
        print(f'Found joystick: "{name}"')
        blacklisted = any(i.match(name) for i in joystick_blacklist)
        if blacklisted:
            print(f'Ignoring joystick: "{name}"')
        else:
            print(f'Configuring joystick: "{name}"')
            joystick.init()
            JOYSTICKS.append(joystick)


# Initialize the game framework
def init() -> None:
    from tuxemon import platform

    platform.init()
    if PLATFORM == "pygame":
        pygame_init()


# Fetches a resource file
# note: this has the potential of being a bottle neck doing to all the checking of paths
# eventually, this should be configured at game launch, or in a config file instead
# of looking all over creation for the required files.
def fetch(*args: str) -> str:
    relative_path = os.path.join(*args)

    for mod_name in CONFIG.mods:
        # when assets are in folder with the source
        path = os.path.join(paths.mods_folder, mod_name, relative_path)
        logger.debug("searching asset: %s", path)
        if os.path.exists(path):
            return path

        # when assets are in a system path (like for os packages and android)
        for root_path in paths.system_installed_folders:
            path = os.path.join(root_path, "mods", mod_name, relative_path)
            logger.debug("searching asset: %s", path)
            if os.path.exists(path):
                return path

        # mods folder is in same folder as the launch script
        path = os.path.join(paths.BASEDIR, "mods", mod_name, relative_path)
        logger.debug("searching asset: %s", path)
        if os.path.exists(path):
            return path

    raise OSError(f"cannot load file {relative_path}")
