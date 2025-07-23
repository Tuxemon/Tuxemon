# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module initializes the display and creates dictionaries of resources.
It contains all the static and dynamic variables used throughout the game such
as display resolution, scale, etc.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from tuxemon import config
from tuxemon.constants import paths

if TYPE_CHECKING:
    import pygame as pg

    SCREEN: pg.surface.Surface
    SCREEN_RECT: pg.rect.Rect
    JOYSTICKS: list[pg.joystick.JoystickType]

logger = logging.getLogger(__name__)


def _compile_joystick_blacklist() -> list[re.Pattern[str]]:
    """Compiles a list of regex patterns for blacklisting joysticks."""
    logger.debug("Compiling joystick blacklist patterns.")
    return [
        re.compile(r"Microsoft.*Transceiver.*"),
        re.compile(r".*Synaptics.*", re.I),
        re.compile(r"Wacom*.", re.I),
    ]


joystick_blacklist = _compile_joystick_blacklist()


def _setup_user_environment() -> config.TuxemonConfig:
    """Sets up user storage directories and loads/saves the game configuration."""
    logger.debug("Setting up user environment and config.")
    try:
        paths.USER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        paths.USER_GAME_DATA_DIR.mkdir(parents=True, exist_ok=True)
        paths.USER_GAME_SAVE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("User directories ensured.")
    except OSError as e:
        logger.critical(f"Failed to create user directories: {e}")
        raise

    config.generate_default_config()
    loaded_config = config.TuxemonConfig(paths.USER_CONFIG_PATH)

    try:
        with paths.USER_CONFIG_PATH.open("w") as fp:
            yaml.dump(
                loaded_config.config, fp, default_flow_style=False, indent=4
            )
        logger.info(
            f"Configuration loaded and saved to {paths.USER_CONFIG_PATH}"
        )
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
    return loaded_config


# How it would be called in the main part of the file:
CONFIG = _setup_user_environment()

# Starting map
STARTING_MAP = "start_"

# Set up the screen size and caption
SCREEN_SIZE = CONFIG.resolution

# Surface Keys (tilesets)
SURFACE_KEYS: list[str] = ["surfable", "walkable", "climbable"]

# frame
FRAME_TIME: float = 0.09

# Set the native tile size so we know how much to scale our maps
# 1 tile = 16 pixels
TILE_SIZE: tuple[int, int] = (16, 16)

# Set the generic icons (eg. party_empty, etc.)
ICON_SIZE: tuple[int, int] = (7, 7)
# Set icons technique (eg. poison, etc.)
TECH_ICON_SIZE: tuple[int, int] = (9, 9)
# Set icons status (eg. poison, etc.)
STATUS_ICON_SIZE: tuple[int, int] = (9, 9)
# set sprite size (eg. nurse, bob, etc.)
SPRITE_SIZE: tuple[int, int] = (16, 32)
# set items size (eg. tuxeball, potion, etc.)
ITEM_SIZE: tuple[int, int] = (24, 24)
# set template size (eg. ceo, adventurer, heroine, etc.)
TEMPLATE_SIZE: tuple[int, int] = (64, 64)
# set monster size (eg. rockitten-front, rockitten-back, etc.)
MONSTER_SIZE: tuple[int, int] = (64, 64)
# set monster menu size (eg. rockitten-menu01, etc.)
MONSTER_SIZE_MENU: tuple[int, int] = (24, 24)
# set borders size (eg dialogues black-orange, etc.)
BORDERS_SIZE: tuple[int, int] = (18, 18)
# set element size (earth, metal, etc.)
ELEMENT_SIZE: tuple[int, int] = (24, 24)
# set island size, battle terrains (grass, etc.)
ISLAND_SIZE: tuple[int, int] = (96, 57)
# set battle background size (grass, etc.)
BATTLE_BG_SIZE: tuple[int, int] = (280, 112)

# Set the healthbar _color
GFX_HP_BAR: str = "gfx/ui/monster/hp_bar.png"
HP_COLOR_FG = (10, 240, 25)  # dark saturated green
HP_COLOR_BG = (245, 10, 25)  # dark saturated red

# Set the XP bar _color
GFX_XP_BAR: str = "gfx/ui/monster/exp_bar.png"
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
UNAVAILABLE_COLOR = (220, 220, 220)
UNAVAILABLE_COLOR_SHOP = (51, 51, 51)
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

# gradients
# Hex 77767b > Hex ffffff (linear + top/bottom)
GRAD_BLACK: str = "gfx/ui/background/gradient_black.png"
# Hex c5e8ea (original)
GRAD_BLUE: str = "gfx/ui/background/gradient_blue.png"
# Hex cdab8f > Hex ffffff (linear + top/bottom)
GRAD_BROWN: str = "gfx/ui/background/gradient_brown.png"
# Hex 8ff0a4 > Hex ffffff (linear + top/bottom)
GRAD_GREEN: str = "gfx/ui/background/gradient_green.png"
# Hex ffbe6f > Hex ffffff (linear + top/bottom)
GRAD_ORANGE: str = "gfx/ui/background/gradient_orange.png"
# Hex f66151 > Hex ffffff (linear + top/bottom)
GRAD_RED: str = "gfx/ui/background/gradient_red.png"
# Hex dc8add > Hex ffffff (linear + top/bottom)
GRAD_VIOLET: str = "gfx/ui/background/gradient_violet.png"
# Hex f9f06b > Hex ffffff (linear + top/bottom)
GRAD_YELLOW: str = "gfx/ui/background/gradient_yellow.png"
# backgrounds
TUX_GENERIC: str = "gfx/ui/background/tux_generic.png"
TUX_INFO: str = "gfx/ui/background/tux_info.png"
ITEM_MENU: str = "gfx/ui/item/item_menu_bg.png"

# background per state
BG_MINIGAME: str = GRAD_BLUE
BG_MISSIONS: str = GRAD_BLUE
BG_PC_KENNEL: str = GRAD_BLUE
BG_PC_LOCKER: str = GRAD_BLUE
BG_PHONE: str = GRAD_BLUE
BG_PHONE_BANKING: str = GRAD_BLUE
BG_PHONE_CONTACTS: str = GRAD_BLUE
BG_PHONE_MAP: str = GRAD_BLUE
BG_START_SCREEN: str = GRAD_BLUE
PYGAME_LOGO: str = "gfx/ui/intro/pygame_logo.png"
CREATIVE_COMMONS: str = "gfx/ui/intro/creative_commons.png"
BG_JOURNAL: str = TUX_GENERIC
BG_JOURNAL_CHOICE: str = TUX_GENERIC
BG_JOURNAL_INFO: str = TUX_INFO
BG_MONSTER_INFO: str = TUX_INFO
BG_PLAYER1: str = "gfx/ui/background/player_info.png"
BG_PLAYER2: str = "gfx/ui/background/player_info1.png"
BG_PARTY: str = "gfx/ui/background/player_info2.png"
BG_ITEMS: str = ITEM_MENU
BG_ITEMS_BACKPACK: str = "gfx/ui/item/backpack.png"
BG_MOVES: str = ITEM_MENU
BG_MONSTERS: str = "gfx/ui/monster/monster_menu_bg.png"

# Native resolution is similar to the old gameboy resolution. This is
# used for scaling.
NATIVE_RESOLUTION: tuple[int, int] = (240, 160)

# Maps
# 1 tile = 1 m (3.28 ft) large
COEFF_TILE: float = 1.0
# for converting metric into imperial (distance)
COEFF_MILES: float = 0.6213711922
COEFF_FEET: float = 0.032808399
# for converting metric into imperial (weight)
COEFF_POUNDS: float = 2.2046

# Players
PLAYER_NPC = CONFIG.player_npc
PLAYER_NAME_LIMIT: int = 15  # The character limit for a player name.
PARTY_LIMIT: int = 6  # The maximum number of tuxemon this npc can hold
#  Moverate limits to avoid losing sprites
MOVERATE_RANGE: tuple[float, float] = (0.0, 20.0)
TRANS_TIME: float = 0.3  # transition time

# PC
U_KM: str = "km"
U_MI: str = "mi"
U_KG: str = "kg"
U_LB: str = "lb"
U_CM: str = "cm"
U_FT: str = "ft"
MUSIC_RANGE: tuple[float, float] = (0.0, 1.0)
SOUND_RANGE: tuple[float, float] = (0.0, 1.0)
MUSIC_LOOP: int = -1
MUSIC_FADEIN: int = 1000  # milliseconds
MUSIC_FADEOUT: int = 1000  # milliseconds
KENNEL: str = "Kennel"
LOCKER: str = "Locker"
MAX_KENNEL: int = 30  # nr max of pc monsters
MAX_LOCKER: int = 30  # nr max of pc items

# Items
MAX_TYPES_BAG: int = 99  # eg 5 capture devices, 1 type and 5 items
# Items menu
MAX_MENU_ITEMS: int = 11

# Monsters
MAX_LEVEL: int = 999
MAX_MOVES: int = 4
MISSING_IMAGE: str = "gfx/sprites/battle/missing.png"
CATCH_RATE_RANGE: tuple[int, int] = (0, 100)
CATCH_RESISTANCE_RANGE: tuple[float, float] = (0.0, 2.0)
# set bond and define range
BOND: int = 25
# set multiplier stats (multiplier: level + coefficient)
COEFF_STATS: int = 7
# set experience required for levelling up
# (level + level_ofs) ** coefficient) - level_ofs default 0
COEFF_EXP: int = 3

# Camera
CAMERA_SHAKE_RANGE: tuple[float, float] = (0.0, 3.0)

# Techniques
RECHARGE_RANGE: tuple[int, int] = (0, 5)
POTENCY_RANGE: tuple[float, float] = (0.0, 1.0)
ACCURACY_RANGE: tuple[float, float] = (0.0, 1.0)
POWER_RANGE: tuple[float, float] = (0.0, 3.0)
HEALING_POWER_RANGE: tuple[float, float] = (0.0, 3.0)

# Combat
MONSTERS_DOUBLE: int = 3  # 3 monsters to trigger 1vs2 or viceversa

# This is the coefficient that can be found in formula.py and
# it calculates the user strength
# eg: user_strength = user.melee * (COEFF_DAMAGE + user.level)
COEFF_DAMAGE: int = 7

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
SAVE_PATH = paths.USER_GAME_SAVE_DIR / "slot"
SAVE_METHOD = "JSON"
# SAVE_METHOD = "CBOR"

DEV_TOOLS = CONFIG.dev_tools


def pygame_init() -> None:
    """Eventually refactor out of prepare."""
    from tuxemon import platform

    platform.init()

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

    T.initialize_translations(recompile=CONFIG.recompile_translations)
    from tuxemon.db import db

    db.load()

    logger.debug("pygame init")
    pg.init()
    pg.display.set_caption(CONFIG.window_caption)

    from tuxemon.platform import is_android

    fullscreen = pg.FULLSCREEN if CONFIG.fullscreen else 0
    if is_android():
        fullscreen = pg.FULLSCREEN
    flags = pg.HWSURFACE | pg.DOUBLEBUF | fullscreen

    if CONFIG.vsync:
        pg.display.set_allow_screensaver()
    SCREEN = pg.display.set_mode(SCREEN_SIZE, flags, vsync=CONFIG.vsync)
    SCREEN_RECT = SCREEN.get_rect()

    # Disable the mouse cursor visibility
    pg.mouse.set_visible(not CONFIG.controller.hide_mouse)

    # Set up any gamepads that we detect
    # The following event types will be generated by the joysticks:
    # JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
    JOYSTICKS = []
    for i in range(pg.joystick.get_count()):
        try:
            joystick = pg.joystick.Joystick(i)
            name = joystick.get_name()
            print(f'Found joystick: "{name}"')
            if any(pattern.match(name) for pattern in joystick_blacklist):
                print(f'Ignoring joystick: "{name}"')
            else:
                print(f'Configuring joystick: "{name}"')
                JOYSTICKS.append(joystick)
        except Exception as e:
            logger.warning(f"Failed to initialize joystick {i}: {e}")


def headless_init() -> None:
    """Initializes game components for a headless environment."""
    from tuxemon.locale import T

    T.initialize_translations(recompile=CONFIG.recompile_translations)
    from tuxemon.db import db

    db.load()
    logger.debug("headless init")


def init(platform: str = "pygame") -> None:
    if platform == "pygame":
        pygame_init()
    elif platform == "headless":
        headless_init()
    else:
        raise ValueError(f"Unsupported platform: {platform}")


# Fetches a resource file
# note: this has the potential of being a bottle neck doing to all the checking of paths
# eventually, this should be configured at game launch, or in a config file instead
# of looking all over creation for the required files.
def fetch(*args: str) -> str:
    relative_path = Path(*args)

    for mod_name in CONFIG.mods:
        # when assets are in folder with the source
        path = paths.mods_folder / mod_name / relative_path
        logger.debug(f"searching asset: {path}")
        if path.exists():
            return path.as_posix()

        # when assets are in a system path (like for OS packages and Android)
        for root_path in paths.system_installed_folders:
            path = root_path / "mods" / mod_name / relative_path
            logger.debug(f"searching asset: {path}")
            if path.exists():
                return path.as_posix()

        # mods folder is in the same folder as the launch script
        path = paths.BASEDIR / "mods" / mod_name / relative_path
        logger.debug(f"searching asset: {path}")
        if path.exists():
            return path.as_posix()

    raise OSError(f"Cannot load file {relative_path}")
