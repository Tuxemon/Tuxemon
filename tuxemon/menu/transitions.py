# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from typing import Protocol

from pygame_menu import Menu

from tuxemon.prepare import DisplayContext


class MenuTransition(Protocol):
    def apply(
        self, menu: Menu, progress: float, context: DisplayContext
    ) -> None: ...


class PopInClamped:
    """Zoom-in animation that scales the menu while clamping size to screen bounds."""

    def __init__(self, max_height_percentage: float = 0.8) -> None:
        self._base_size: tuple[int, int] | None = None
        self.max_height_percentage = max_height_percentage

    def apply(
        self, menu: Menu, progress: float, context: DisplayContext
    ) -> None:

        if self._base_size is None:
            size = menu.get_size(widget=True)
            self._base_size = (int(size[0]), int(size[1]))

        assert self._base_size is not None
        base_w, base_h = self._base_size

        screen_w, screen_h = context.resolution

        # Clamp base size to screen bounds
        base_w = min(base_w, screen_w)
        base_h = min(base_h, int(screen_h * self.max_height_percentage))

        # Avoid zero scale
        scale = max(0.01, progress)

        w = max(1, int(base_w * scale))
        h = max(1, int(base_h * scale))

        menu.resize(w, h)


class SlideRight:
    """Slide the menu in from the right edge of the screen."""

    def __init__(self) -> None:
        self._width: int | None = None

    def apply(
        self, menu: Menu, progress: float, context: DisplayContext
    ) -> None:

        if self._width is None:
            self._width = menu.get_width(border=True)

        # Original behavior:
        # animation_offset = width * progress
        # menu.translate(-animation_offset, 0)
        offset = -int(self._width * progress)

        menu.translate(offset, 0)


class EaseOut:
    """Easing curve that accelerates quickly and slows toward the end."""

    def __call__(self, t: float) -> float:
        return math.sin(t * math.pi / 2)
