from __future__ import annotations

from typing import List, Literal, Optional, Tuple, Union

import pygame
from pygame.rect import Rect

from tuxemon.graphics import ColorLike
from tuxemon.sprite import Sprite
from tuxemon.ui import draw

min_font_size = 7


class TextArea(Sprite):
    """Area of the screen that can draw text."""

    animated = True

    def __init__(
        self,
        font: pygame.font.Font,
        font_color: ColorLike,
        bg: ColorLike = (192, 192, 192),
    ) -> None:
        super().__init__()
        self.rect = Rect(0, 0, 0, 0)
        self.drawing_text = False
        self.font = font
        self.font_color = font_color
        self.font_bg = bg
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
                self.font_bg,
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

    def _start_text_animation(self) -> None:
        self.drawing_text = True
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._iter = draw.iter_render_text(
            self._text,
            self.font,
            self.font_color,
            self.font_bg,
            self.image.get_rect(),
        )


def draw_text(
    surface: pygame.surface.Surface,
    text: str,
    rect: Union[Rect, Tuple[int, int, int, int]],
    *,
    justify: Literal["left", "center", "right"] = "left",
    align: Literal["top", "middle", "bottom"] = "top",
    font: pygame.font.Font,
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

    if not font_color:
        font_color = (0, 0, 0)

    if not text:
        return

    # Create a text surface so we can determine how many pixels
    # wide each character is
    text_surface = font.render(text, True, font_color)

    # Calculate the number of pixels per letter based on the size
    # of the text and the number of characters in the text
    pixels_per_letter = text_surface.get_width() / len(text)

    # Create a list of the lines of text as well as a list of the
    # individual words so we can check each line's length in pixels
    lines: List[str] = []
    wordlist: List[str] = []

    # Loop through each word in the text and add it to the word list
    for word in text.split():

        # If there is a linebreak in this word, then split it up into a list separated by \n
        if "\\n" in word:
            w = word.split("\\n")

            # Loop through the list and every time we encounter a blank string, then that is
            # a new line. So we append the current line and reset the word list for a new line
            for item in w:
                if item == "":
                    # This is a new line!
                    lines.append(" ".join(wordlist))
                    wordlist = []
                # If we encounter an actual word, then just append it to the word list
                else:
                    wordlist.append(item)

        # If there's no line break, continue normally to word wrap
        else:

            # Append the word to the current line
            wordlist.append(word)

            # Here, we convert the list into a string separated by spaces and multiply
            # the number of characters in the string by the number of pixels per letter
            # that we calculated earlier. This will let us know how large the text will
            # be in pixels.
            if len(" ".join(wordlist)) * pixels_per_letter > width:
                # If the size exceeds the width of the menu, then append the line to the
                # list of lines, but stripping off the last word we added (because this
                # was the word that made us exceed the menubox's size.
                lines.append(" ".join(wordlist[:-1]))

                # Reset the wordlist for the next line and add the word we stripped off
                wordlist = []
                wordlist.append(word)

    # If the last line is not blank, then append it to the list
    if " ".join(wordlist) != "":
        lines.append(" ".join(wordlist))

    # If the justification was set, handle the position of the text automatically
    if justify == "center":
        if lines:
            left = (left + (width / 2)) - (
                (len(lines[0]) * pixels_per_letter) / 2
            )
        else:
            left = 0

    elif justify == "right":
        raise NotImplementedError("Needs to be implemented")

    # If text alignment was set, handle the position of the text automatically
    if align == "middle":
        top = (top + (height / 2)) - (
            (text_surface.get_height() * len(lines)) / 2
        )

    elif align == "bottom":
        raise NotImplementedError("Needs to be implemented")

    # Set a spacing variable that we will add to to space each line.
    spacing = 0
    for item in lines:
        line = font.render(item, True, font_color)

        surface.blit(line, (left, top + spacing))
        spacing += line.get_height()  # + self.line_spacing
