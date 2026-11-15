# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from functools import lru_cache
from typing import TYPE_CHECKING

from pygame import SRCALPHA
from pygame.font import Font
from pygame.surface import Surface

from tuxemon.graphics import ColorLike
from tuxemon.platform.const.graphics import FONT_SHADOW_COLOR, FONT_SIZE

if TYPE_CHECKING:
    from tuxemon.scaling import ScalingStrategy


class TextRenderer:
    def __init__(
        self,
        scaling: ScalingStrategy,
        font_color: ColorLike,
        font_shadow_color: ColorLike | None = None,
        font_filename: str | None = None,
        font: Font | None = None,
    ) -> None:
        self.scaling = scaling
        self.font_color = font_color
        self.font_shadow_color = font_shadow_color or FONT_SHADOW_COLOR
        self.font = font or Font(
            font_filename, self.scaling.scale_int(FONT_SIZE)
        )

        ox, oy = self.scaling.scale_sequence((0.5, 0.5))
        self._shadow_offset: tuple[float, ...] = (float(ox), float(oy))

    @lru_cache(maxsize=256)
    def _render_glyph(
        self,
        char: str,
        fg: tuple[int, ...],
        bg: tuple[int, ...],
    ) -> Surface:
        fg_surf = self.font.render(char, True, fg)
        bg_surf = self.font.render(char, True, bg)

        ox, oy = self._shadow_offset
        w, h = fg_surf.get_size()

        surf = Surface((int(w + ox), int(h + oy)), SRCALPHA)
        surf.blit(bg_surf, (ox, oy))
        surf.blit(fg_surf, (0, 0))
        return surf

    def get_glyph(
        self,
        char: str,
        fg: ColorLike | None = None,
        bg: ColorLike | None = None,
    ) -> Surface:
        fg_color: ColorLike = fg or self.font_color
        bg_color: ColorLike = bg or self.font_shadow_color

        fg_key = tuple(fg_color)
        bg_key = tuple(bg_color)

        return self._render_glyph(char, fg_key, bg_key)

    def shadow_text(
        self,
        text: str,
        bg: ColorLike | None = None,
        fg: ColorLike | None = None,
        offset: tuple[float, ...] | None = None,
    ) -> Surface:
        fg = fg or self.font_color
        bg = bg or self.font_shadow_color

        if offset is None:
            offset = self._shadow_offset
        else:
            if not (isinstance(offset, (tuple, list)) and len(offset) == 2):
                raise TypeError("offset must be a tuple of two numbers")
            offset = tuple(self.scaling.scale_sequence(offset))

        font_color = self.font.render(text, True, fg)
        shadow_color = self.font.render(text, True, bg)

        size = [
            int(math.ceil(a + b))
            for a, b in zip(offset, font_color.get_size())
        ]
        image = Surface(size, SRCALPHA)
        image.blit(shadow_color, tuple(offset))
        image.blit(font_color, (0, 0))
        return image
