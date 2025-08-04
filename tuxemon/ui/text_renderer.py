# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Optional

from pygame import SRCALPHA
from pygame.font import Font
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.graphics import ColorLike
from tuxemon.tools import scale


def create_layout(
    scale: float,
) -> Callable[[Sequence[float]], Sequence[float]]:
    def func(area: Sequence[float]) -> Sequence[float]:
        return [scale * i for i in area]

    return func


layout = create_layout(prepare.SCALE)


class TextRenderer:
    def __init__(
        self,
        font_color: ColorLike,
        font_shadow_color: Optional[ColorLike] = None,
        font_filename: Optional[str] = None,
        font: Optional[Font] = None,
    ) -> None:
        self.font_color = font_color
        if font_shadow_color is None:
            font_shadow_color = prepare.FONT_SHADOW_COLOR
        self.font_shadow_color = font_shadow_color
        self.font = font or Font(font_filename, scale(prepare.FONT_SIZE))

    def shadow_text(
        self,
        text: str,
        bg: Optional[ColorLike] = None,
        fg: Optional[ColorLike] = None,
        offset: tuple[float, float] = (0.5, 0.5),
    ) -> Surface:
        """
        Render shadowed text using the current font and shadow color settings.

        Parameters:
            text: The text string to render.
            bg: Shadow color. If None, uses the default font shadow color.
            fg: Foreground font color. If None, uses the default font color.
            offset: Tuple representing the x and y shadow offset in pixels.

        Returns:
            A Surface containing the rendered text with its shadow applied.
        """
        if not fg:
            fg = self.font_color
        if not bg:
            bg = self.font_shadow_color
        font_color = self.font.render(text, True, fg)
        shadow_color = self.font.render(text, True, bg)
        _offset = layout(offset)
        size = [
            int(math.ceil(a + b))
            for a, b in zip(_offset, font_color.get_size())
        ]
        image = Surface(size, SRCALPHA)
        image.blit(shadow_color, tuple(_offset))
        image.blit(font_color, (0, 0))
        return image
