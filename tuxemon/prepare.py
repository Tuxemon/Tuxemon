# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module initializes the display, pygame, translations, and databases."""

from __future__ import annotations

import logging
import os
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field

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


def _identity_point(pos: tuple[float, float]) -> tuple[int, int]:
    return int(pos[0]), int(pos[1])


@dataclass
class DisplayContext:
    screen: pg.Surface
    rect: pg.Rect
    resolution: tuple[int, int]
    tile_size: tuple[int, int]
    scale: int
    scaling: ScalingStrategy
    window_size: tuple[int, int] = (1, 1)
    gpu_upscaling: bool = False
    window_to_screen: Callable[[tuple[float, float]], tuple[int, int]] = (
        field(default=_identity_point)
    )


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

    from tuxemon.platform import platform

    fullscreen = CONFIG.fullscreen or platform.is_android()

    if CONFIG.vsync:
        pg.display.set_allow_screensaver()

    context = None
    if CONFIG.upscaler == "gpu":
        try:
            context = _init_gpu_display(fullscreen)
        except Exception:
            logger.exception(
                "GPU upscaler failed to start, falling back to CPU upscaler"
            )
            pg.display.quit()
            pg.display.init()
            pg.display.set_caption(CONFIG.window_caption)

    if context is None:
        context = _init_cpu_display(fullscreen)

    pg.mouse.set_visible(not CONFIG.controller.hide_mouse)

    DISPLAY_CONTEXT = context
    return DISPLAY_CONTEXT


def _init_cpu_display(fullscreen: bool) -> DisplayContext:
    scaling = make_default_scaling(CONFIG, NATIVE_RESOLUTION)

    flags = pg.HWSURFACE | pg.DOUBLEBUF
    if fullscreen:
        flags |= pg.FULLSCREEN

    screen = pg.display.set_mode(CONFIG.resolution, flags, vsync=CONFIG.vsync)

    return DisplayContext(
        screen=screen,
        rect=screen.get_rect(),
        resolution=CONFIG.resolution,
        tile_size=scaling.scale_point(NATIVE_TILE_SIZE),
        scale=scaling._scale,
        scaling=scaling,
        window_size=CONFIG.resolution,
    )


@dataclass(frozen=True)
class FrameFit:
    frame_size: tuple[int, int]
    stretch: float
    offset_x: int
    offset_y: int

    @classmethod
    def compute(
        cls, window_size: tuple[int, int], frame_size: tuple[int, int]
    ) -> FrameFit:
        frame_w, frame_h = frame_size
        stretch = min(window_size[0] / frame_w, window_size[1] / frame_h)
        offset_x = round((window_size[0] / stretch - frame_w) / 2)
        offset_y = round((window_size[1] / stretch - frame_h) / 2)
        return cls(frame_size, stretch, offset_x, offset_y)

    def window_to_screen(self, pos: tuple[float, float]) -> tuple[int, int]:
        x = int(pos[0] / self.stretch - self.offset_x)
        y = int(pos[1] / self.stretch - self.offset_y)
        return (
            max(0, min(self.frame_size[0] - 1, x)),
            max(0, min(self.frame_size[1] - 1, y)),
        )


def gpu_render_scale(requested: int) -> int:
    return max(1, min(8, requested))


def _init_gpu_display(fullscreen: bool) -> DisplayContext:
    from pygame._sdl2.video import Renderer, Window

    scale = gpu_render_scale(CONFIG.gpu_render_scale)
    internal = (NATIVE_RESOLUTION[0] * scale, NATIVE_RESOLUTION[1] * scale)

    os.environ["PYGAME_FORCE_SCALE"] = (
        "photo" if CONFIG.gpu_smoothing else "default"
    )

    flags = pg.SCALED
    if fullscreen:
        flags |= pg.FULLSCREEN

    screen = pg.display.set_mode(internal, flags, vsync=CONFIG.vsync)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        window = Window.from_display_module()

    if not fullscreen:
        window.size = CONFIG.resolution
        window.position = pg.WINDOWPOS_CENTERED

    renderer = Renderer.from_window(window)
    window_w, window_h = window.size
    fit = FrameFit.compute((window_w, window_h), internal)

    renderer.logical_size = (0, 0)
    renderer.scale = (fit.stretch, fit.stretch)
    renderer.set_viewport(
        pg.Rect(fit.offset_x, fit.offset_y, internal[0], internal[1])
    )

    logger.info(
        f"GPU upscaler: drawing at {internal[0]}x{internal[1]}, "
        f"stretched x{fit.stretch:.2f} to {window_w}x{window_h}"
    )

    scaling = DefaultScaling(scale)
    return DisplayContext(
        screen=screen,
        rect=screen.get_rect(),
        resolution=internal,
        tile_size=scaling.scale_point(NATIVE_TILE_SIZE),
        scale=scale,
        scaling=scaling,
        window_size=(window_w, window_h),
        gpu_upscaling=True,
        window_to_screen=fit.window_to_screen,
    )


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
        window_size=CONFIG.resolution,
    )

    return DISPLAY_CONTEXT


def core_init() -> None:
    from tuxemon.database.runtime import db
    from tuxemon.locale.locale import T

    T.initialize_translations(recompile=CONFIG.recompile_translations)
    db.load()
    logger.debug("Initializing core systems")
