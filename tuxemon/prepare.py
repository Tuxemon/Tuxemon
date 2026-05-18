# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module initializes the display, pygame, translations, and databases."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import pygame as pg

from tuxemon.platform.const.sizes import NATIVE_RESOLUTION
from tuxemon.platform.const.sizes import TILE_SIZE as NATIVE_TILE_SIZE
from tuxemon.scaling import (
    DefaultScaling,
    ScalingStrategy,
    make_default_scaling,
)
from tuxemon.user_config import CONFIG

logger = logging.getLogger(__name__)


@dataclass
class DisplayContext:
    screen: pg.Surface
    rect: pg.Rect
    resolution: tuple[int, int]
    tile_size: tuple[int, int]
    scale: int
    scaling: ScalingStrategy


_default_surface = pg.Surface((1, 1))
_default_rect = _default_surface.get_rect()

DISPLAY_CONTEXT: DisplayContext = DisplayContext(
    screen=_default_surface,
    rect=_default_rect,
    resolution=(1, 1),
    tile_size=(1, 1),
    scale=1,
    scaling=DefaultScaling(1),
)


DEV_TOOLS = CONFIG.dev_tools


def pygame_init() -> DisplayContext:
    """Initializes Pygame, display, translations, and databases."""
    global DISPLAY_CONTEXT

    core_init()

    logger.debug("pygame init")
    pg.init()
    pg.display.set_caption(CONFIG.window_caption)

    scaling = make_default_scaling(CONFIG, NATIVE_RESOLUTION)

    # Fullscreen flags
    fullscreen = pg.FULLSCREEN if CONFIG.fullscreen else 0

    from tuxemon.platform import platform

    if platform.is_android():
        fullscreen = pg.FULLSCREEN

    flags = pg.HWSURFACE | pg.DOUBLEBUF | fullscreen

    if CONFIG.vsync:
        pg.display.set_allow_screensaver()

    screen = pg.display.set_mode(CONFIG.resolution, flags, vsync=CONFIG.vsync)
    rect = screen.get_rect()

    pg.mouse.set_visible(not CONFIG.controller.hide_mouse)

    DISPLAY_CONTEXT = DisplayContext(
        screen=screen,
        rect=rect,
        resolution=CONFIG.resolution,
        tile_size=scaling.scale_point(NATIVE_TILE_SIZE),
        scale=scaling._scale,
        scaling=scaling,
    )

    return DISPLAY_CONTEXT


def headless_init() -> DisplayContext:
    """Initializes game components for a headless environment."""
    global DISPLAY_CONTEXT

    logger.debug("headless init")

    os.environ["SDL_VIDEODRIVER"] = "dummy"

    core_init()

    pg.display.init()
    pg.font.init()

    screen = pg.Surface(CONFIG.resolution)
    rect = screen.get_rect()

    DISPLAY_CONTEXT = DisplayContext(
        screen=screen,
        rect=rect,
        resolution=CONFIG.resolution,
        tile_size=NATIVE_TILE_SIZE,
        scale=1,
        scaling=DefaultScaling(1),
    )

    return DISPLAY_CONTEXT


def core_init() -> None:
    from tuxemon.database.runtime import db
    from tuxemon.locale.locale import T

    T.initialize_translations(recompile=CONFIG.recompile_translations)
    db.load()
    logger.debug("Initializing core systems")
