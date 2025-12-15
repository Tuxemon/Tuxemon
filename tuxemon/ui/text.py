# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Iterator
from typing import Optional, Union

from pygame import SRCALPHA
from pygame.draw import line, rect
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.graphics import ColorLike
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


class TextAreaDiagnostics:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.border_color = (255, 0, 0, 128)
        self.line_color = (255, 0, 0, 80)
        self.maxline_color = (0, 255, 255, 60)
        self.text_color = (200, 200, 200)

    def draw_outline(self, surface: Surface) -> None:
        if not self.enabled:
            return
        rect(surface, self.border_color, surface.get_rect(), width=5)

    def draw_line_guides(self, surface: Surface, font: Font) -> None:
        if not self.enabled:
            return
        line_height = get_font_height(font)
        for i in range(surface.get_height() // line_height):
            y = i * line_height
            line(
                surface,
                self.line_color,
                (0, y),
                (surface.get_width(), y),
                width=5,
            )

    def draw_maxline_guides(self, surface: Surface, font: Font) -> None:
        if not self.enabled:
            return
        max_lines = surface.get_height() // get_font_height(font)
        for i in range(max_lines):
            y = i * get_font_height(font)
            line(
                surface,
                self.maxline_color,
                (0, y),
                (surface.get_width(), y),
                width=5,
            )


class TextArea(Sprite):
    """Area of the screen that can draw text."""

    animated = True

    def __init__(
        self,
        font: Font,
        font_color: ColorLike,
        font_shadow: ColorLike = prepare.FONT_SHADOW_COLOR,
        background_color: Optional[ColorLike] = None,
        background_image: Optional[Surface] = None,
        h_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
        v_alignment: VerticalAlignment = VerticalAlignment.TOP,
        overflow_behavior: TextOverflow = TextOverflow.CLIP,
        debug_rendering: bool = False,
        line_spacing: int = 0,
    ) -> None:
        super().__init__()
        self.rect = Rect(0, 0, 0, 0)
        self.drawing_text = False
        self.font = font
        self.font_color = font_color
        self.font_shadow = font_shadow
        self._text_renderer = TextRenderer(
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
        self._rendered_text = None
        self._text_rect = None
        self._text = ""
        self._iter: Optional[Iterator[RenderedChar]] = None

    def __iter__(self) -> TextArea:
        return self

    def __len__(self) -> int:
        return len(self._text)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value == self._text:
            return

        self._text = value

        if not self._text:
            self.drawing_text = False
            self.image = Surface(self.rect.size, SRCALPHA)
            return

        if self.animated:
            self._start_text_animation()
        else:
            self.image = self._text_renderer.shadow_text(self._text)

    def __next__(self) -> None:
        if self.animated:
            if self._iter is None:
                self.drawing_text = False
                raise StopIteration
            try:
                rendered_char = next(self._iter)
                self.image.blit(rendered_char.surface, rendered_char.rect)
            except StopIteration:
                self.drawing_text = False
                raise
        else:
            raise StopIteration

    def set_overflow_behavior(self, behavior: TextOverflow) -> None:
        self.overflow_behavior = behavior

    def set_background(
        self,
        background_color: Optional[ColorLike] = None,
        background_image: Optional[Surface] = None,
    ) -> None:
        self.image = Surface(self.rect.size, SRCALPHA)

        if background_color:
            self.image.fill(background_color)
        if background_image:
            self.image.blit(background_image, (0, 0))

    def _start_text_animation(self) -> None:
        self.drawing_text = True
        self.image = Surface(self.rect.size, SRCALPHA)

        if self.background_color:
            self.image.fill(self.background_color)
        if self.background_image:
            self.image.blit(self.background_image, (0, 0))

        self.diagnostics.draw_outline(self.image)
        self.diagnostics.draw_line_guides(self.image, self.font)
        self.diagnostics.draw_maxline_guides(self.image, self.font)

        self._iter = iter_render_text(
            text=self._text,
            font=self.font,
            fg=self.font_color,
            bg=self.font_shadow,
            rect=self.image.get_rect(),
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
    rect: Union[Rect, tuple[int, int, int, int]],
    *,
    h_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
    v_alignment: VerticalAlignment = VerticalAlignment.TOP,
    font: Font,
    font_size: Optional[int] = None,
    font_color: Optional[ColorLike] = None,
    text_renderer: Optional[TextRenderer] = None,
) -> None:
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
        font_color: (Optional) The color of the font. Defaults to prepare.FONT_COLOR if None.
        text_renderer: (Optional) An existing TextRenderer instance. If None, one will be created.
    """
    rect_obj = Rect(rect) if isinstance(rect, tuple) else rect

    if rect_obj.width <= 0 or rect_obj.height <= 0:
        return

    if not font_color:
        font_color = prepare.FONT_COLOR

    if text_renderer is None:
        text_renderer = TextRenderer(font_color=font_color, font=font)

    if not text:
        return

    ml_renderer = MultilineTextRenderer(text_renderer)
    line_surfaces_data = ml_renderer.render_lines(text, rect_obj.width)

    if not line_surfaces_data:
        return

    total_text_height = sum(height for _, height in line_surfaces_data)
    total_text_width = 0
    if line_surfaces_data:
        total_text_width = max(s.get_width() for s, _ in line_surfaces_data)

    offset_x, offset_y = calculate_alignment_offset(
        rect_obj, total_text_width, total_text_height, h_alignment, v_alignment
    )

    current_draw_y = rect_obj.top + offset_y

    for text_surface, line_height in line_surfaces_data:
        blit_position = (rect_obj.left + offset_x, current_draw_y)
        surface.blit(text_surface, blit_position)
        current_draw_y += line_height
