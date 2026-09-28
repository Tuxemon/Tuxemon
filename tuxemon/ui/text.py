# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from pygame import SRCALPHA
from pygame.draw import line, rect
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.graphics import ColorLike
from tuxemon.platform.const.graphics import FONT_COLOR, FONT_SHADOW_COLOR
from tuxemon.sprite import Sprite
from tuxemon.ui.draw import (
    RenderedChar,
    TextOverflow,
    break_text_into_lines,
    calculate_alignment_offset,
    get_font_height,
    iter_render_text,
)
from tuxemon.ui.text_alignment import HorizontalAlignment, VerticalAlignment
from tuxemon.ui.text_renderer import TextRenderer

if TYPE_CHECKING:
    from tuxemon.scaling import ScalingStrategy

logger = logging.getLogger(__name__)


class TextAreaDiagnostics:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.border_color = (255, 0, 0, 128)
        self.line_color = (255, 0, 0, 80)
        self.maxline_color = (0, 255, 255, 120)

    def draw(self, surface: Surface, font: Font) -> None:
        if not self.enabled:
            return

        rect(surface, self.border_color, surface.get_rect(), width=2)

        line_height = get_font_height(font)
        h = surface.get_height()
        w = surface.get_width()

        for y in range(0, h, line_height):
            line(surface, self.line_color, (0, y), (w, y), width=1)

        last_y = (h // line_height - 1) * line_height
        line(surface, self.maxline_color, (0, last_y), (w, last_y), width=2)


class TextArea(Sprite):
    animated = True

    def __init__(
        self,
        font: Font,
        font_color: ColorLike,
        rect: Rect,
        scaling: ScalingStrategy,
        font_shadow: ColorLike = FONT_SHADOW_COLOR,
        background_color: ColorLike | None = None,
        background_image: Surface | None = None,
        h_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
        v_alignment: VerticalAlignment = VerticalAlignment.TOP,
        overflow_behavior: TextOverflow = TextOverflow.CLIP,
        debug_rendering: bool = False,
        line_spacing: int = 0,
    ) -> None:
        super().__init__()
        self.rect = rect.copy()
        self.image = Surface(self.rect.size, SRCALPHA)
        self.drawing_text = False

        self.font = font
        self.font_color = font_color
        self.font_shadow = font_shadow
        self.scaling = scaling

        self._text_renderer = TextRenderer(
            scaling=scaling,
            font=self.font,
            font_color=self.font_color,
            font_shadow_color=self.font_shadow,
        )

        self.background_color = background_color
        self.background_image = background_image
        self.h_alignment = h_alignment
        self.v_alignment = v_alignment
        self.overflow_behavior = overflow_behavior
        self.line_spacing = line_spacing

        self.diagnostics = TextAreaDiagnostics(enabled=debug_rendering)

        self._text = ""
        self._iter: Iterator[RenderedChar] | None = None

    def _render_background(self) -> Surface:
        surf = Surface(self.rect.size, SRCALPHA)
        if self.background_color:
            surf.fill(self.background_color)
        if self.background_image:
            surf.blit(self.background_image, (0, 0))
        return surf

    def _render_base_layer(self) -> Surface:
        base = self._render_background()
        self.diagnostics.draw(base, self.font)
        return base

    def _render_static_text(self) -> None:
        base = self._render_base_layer()
        text_surface = self._text_renderer.shadow_text(self._text)
        base.blit(text_surface, (0, 0))
        self.image = base

    def __iter__(self) -> TextArea:
        return self

    def __next__(self) -> None:
        if not self.animated:
            raise StopIteration
        if self._iter is None:
            self.drawing_text = False
            raise StopIteration
        try:
            rendered_char = next(self._iter)
            self.image.blit(rendered_char.surface, rendered_char.rect)
        except StopIteration:
            self.drawing_text = False
            raise

    def __len__(self) -> int:
        return len(self._text)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:

        self._text = value

        if not self._text:
            self.drawing_text = False
            self.image = Surface(self.rect.size, SRCALPHA)
            return

        if self.animated:
            self._start_text_animation()
        else:
            self._render_static_text()

    def set_overflow_behavior(self, behavior: TextOverflow) -> None:
        self.overflow_behavior = behavior

    def _start_text_animation(self) -> None:
        self.drawing_text = True
        self.image = self._render_base_layer()

        self._iter = iter_render_text(
            text=self._text,
            font=self.font,
            fg=self.font_color,
            bg=self.font_shadow,
            rect=self.image.get_rect(),
            scaling=self.scaling,
            h_alignment=self.h_alignment,
            v_alignment=self.v_alignment,
            text_renderer=self._text_renderer,
            overflow_behavior=self.overflow_behavior,
            line_spacing=self.line_spacing,
        )


class MultilineTextRenderer:
    def __init__(
        self,
        text_renderer: TextRenderer,
        line_spacing: int = 0,
    ) -> None:
        self.text_renderer = text_renderer
        self.line_spacing = line_spacing
        self.font = text_renderer.font

    def render_lines(
        self, text: str, max_width: int
    ) -> list[tuple[Surface, int]]:
        """
        Renders text into a list of Pygame Surfaces, one for each line.
        It uses the shared `break_text_into_lines` utility for word wrapping.

        Parameters:
            text: The input text. Newline characters (`\n`) are treated as paragraph breaks.
                If the text contains literal sequences like `\\n`, they will be interpreted
                and converted into actual line breaks internally before processing.
            max_width: The maximum width in pixels for wrapping.

        Returns:
            A list of tuples, where each tuple contains (Surface, height) for a line.
            Heights include any added line_spacing.
        """
        if not text:
            return []

        text = text.replace("\\n", "\n")

        string_lines: list[str] = list(
            break_text_into_lines(
                text, self.font, max_width, allow_word_overflow=False
            )
        )

        rendered_surfaces_with_heights = []
        for i, line_text in enumerate(string_lines):
            line_surface: Surface

            if not line_text:
                line_surface = self.text_renderer.shadow_text(
                    " ",
                    fg=self.text_renderer.font_color,
                    bg=self.text_renderer.font_shadow_color,
                )
            else:
                line_surface = self.text_renderer.shadow_text(
                    line_text,
                    fg=self.text_renderer.font_color,
                    bg=self.text_renderer.font_shadow_color,
                )

            rendered_surfaces_with_heights.append(
                (line_surface, line_surface.get_height())
            )

            if self.line_spacing > 0 and i < len(string_lines) - 1:
                spacing_surface = Surface(
                    (max_width, self.line_spacing), SRCALPHA
                )
                rendered_surfaces_with_heights.append(
                    (spacing_surface, self.line_spacing)
                )

        return rendered_surfaces_with_heights


def draw_text(
    surface: Surface,
    text: str,
    rect: Rect | tuple[int, int, int, int],
    scaling: ScalingStrategy,
    *,
    h_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
    v_alignment: VerticalAlignment = VerticalAlignment.TOP,
    font: Font,
    font_size: int | None = None,
    font_color: ColorLike | None = None,
    text_renderer: TextRenderer | None = None,
    return_metrics: bool = False,
) -> dict[str, Any] | None:
    """
    Draws text to a surface within a specified rectangle, handling wrapping and alignment.

    If the text exceeds the rect size, it will autowrap. To place text on a
    new line, put TWO newline characters (\\n)  in your text.

    Parameters:
        surface: The Pygame Surface to draw the text onto.
        text: The text string to draw.
        rect: The area (Rect or tuple) where the text will be placed.
        h_alignment: Horizontal alignment preference (LEFT, CENTER, RIGHT).
        v_alignment: Vertical alignment preference (TOP, CENTER, BOTTOM).
        font: The Pygame Font object to use for rendering.
        font_size: (Optional) Not directly used if a Font object is provided, but kept for API.
        font_color: (Optional) The color of the font. Defaults to FONT_COLOR if None.
        text_renderer: (Optional) An existing TextRenderer instance. If None, one will be created.
    """
    rect_obj = Rect(rect) if isinstance(rect, tuple) else rect

    if rect_obj.width <= 0 or rect_obj.height <= 0:
        return None

    if font_color is None:
        font_color = FONT_COLOR

    if text_renderer is None:
        text_renderer = TextRenderer(
            scaling=scaling, font_color=font_color, font=font
        )

    if not text:
        return None

    ml_renderer = MultilineTextRenderer(text_renderer)
    line_surfaces_data = ml_renderer.render_lines(text, rect_obj.width)

    if not line_surfaces_data:
        return None

    total_text_height = sum(height for _, height in line_surfaces_data)
    total_text_width = max(s.get_width() for s, _ in line_surfaces_data)

    offset_x, offset_y = calculate_alignment_offset(
        rect_obj, total_text_width, total_text_height, h_alignment, v_alignment
    )

    current_draw_y = rect_obj.top + offset_y

    for text_surface, line_height in line_surfaces_data:
        blit_position = (rect_obj.left + offset_x, current_draw_y)
        surface.blit(text_surface, blit_position)
        current_draw_y += line_height

    if return_metrics:
        return {
            "rect": Rect(
                rect_obj.left + offset_x,
                rect_obj.top + offset_y,
                total_text_width,
                total_text_height,
            ),
            "offset": (offset_x, offset_y),
            "lines": line_surfaces_data,
        }

    return None
