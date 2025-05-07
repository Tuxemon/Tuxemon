# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Literal, Optional, Union

from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.graphics import ColorLike
from tuxemon.sprite import Sprite
from tuxemon.ui import draw

min_font_size = 7


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
        alignment: str = "left",
        vertical_alignment: str = "top",
    ) -> None:
        super().__init__()
        self.rect = Rect(0, 0, 0, 0)
        self.drawing_text = False
        self.font = font
        self.font_color = font_color
        self.font_shadow = font_shadow
        self.background_color = background_color
        self.background_image = background_image
        self.alignment = alignment
        self.vertical_alignment = vertical_alignment
        self._rendered_text = None
        self._text_rect = None
        self._text = ""

    def __iter__(self) -> TextArea:
        return self

    def __len__(self) -> int:
        return len(self._text)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value

        if self.animated:
            self._start_text_animation()
        else:
            self.image = draw.shadow_text(
                self.font,
                self.font_color,
                self.font_shadow,
                self._text,
            )

    def __next__(self) -> None:
        if self.animated:
            try:
                dest, scrap = next(self._iter)
                self.image.blit(scrap, dest)
            except StopIteration:
                self.drawing_text = False
                raise
        else:
            raise StopIteration

    next = __next__

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

        self._iter = draw.iter_render_text(
            text=self._text,
            font=self.font,
            fg=self.font_color,
            bg=self.font_shadow,
            rect=self.image.get_rect(),
            alignment=self.alignment,
            vertical_alignment=self.vertical_alignment,
        )


def draw_text(
    surface: Surface,
    text: str,
    rect: Union[Rect, tuple[int, int, int, int]],
    *,
    justify: Literal["left", "center", "right"] = "left",
    align: Literal["top", "middle", "bottom"] = "top",
    font: Font,
    font_size: Optional[int] = None,
    font_color: Optional[ColorLike] = None,
) -> None:
    """
    Draws text to a surface.

    If the text exceeds the rect size, it will autowrap. To place text on a
    new line, put TWO newline characters (\\n)  in your text.

    Parameters:
        text: The text that you want to draw to the current menu item.
        rect: Area where the text will be placed.
        justify: Left, center, or right justify the text.
        align: Align the text to the top, middle, or bottom of the menu.
        font: Font to use to draw the text.
        font_size: Size of the font in pixels BEFORE scaling is done. *Default: 4*
        font_color: Tuple of RGB values of the font _color to use.

    .. image:: images/menu/justify_center.png
    """
    left, top, width, height = rect
    _left: float = left
    _top: float = top

    if not font_color:
        font_color = prepare.FONT_COLOR

    if not text:
        return

    # Create a list of lines of text
    lines: list[str] = []
    wordlist: list[str] = []
    text_surface = font.render(text, True, font_color)
    pixels_per_letter = text_surface.get_width() / len(text)

    # Word wrapping logic
    for word in text.split():
        if "\\n" in word:
            w = word.split("\\n")
            for item in w:
                if item == "":
                    lines.append(" ".join(wordlist))
                    wordlist = []
                else:
                    wordlist.append(item)
        else:
            wordlist.append(word)
            if len(" ".join(wordlist)) * pixels_per_letter > width:
                lines.append(" ".join(wordlist[:-1]))
                wordlist = [word]
    if " ".join(wordlist) != "":
        lines.append(" ".join(wordlist))

    # Calculate vertical alignment (align)
    total_text_height = len(lines) * text_surface.get_height()
    if align == "middle":
        _top = top + (height - total_text_height) / 2
    elif align == "bottom":
        _top = top + height - total_text_height

    # Set a spacing variable that we will add to space each line.
    spacing = 0
    for line in lines:
        line_surface = font.render(line, True, font_color)
        line_width = line_surface.get_width()

        if justify == "center":
            _left = left + (width - line_width) / 2
        elif justify == "right":
            _left = left + width - line_width
        else:
            _left = left

        surface.blit(line_surface, (_left, _top + spacing))
        spacing += line_surface.get_height()
