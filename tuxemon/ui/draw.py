from __future__ import annotations
import logging
import math
from itertools import product

import pygame

from pygame.rect import Rect

from tuxemon import prepare
from tuxemon.graphics import ColorLike
from tuxemon.sprite import Sprite
from typing import Callable, Sequence, Optional, Tuple, Generator, Iterable,\
    List

logger = logging.getLogger(__name__)

__all__ = ("GraphicBox", "draw_text")


def create_layout(
    scale: float,
) -> Callable[[Sequence[float]], Sequence[float]]:
    def func(area: Sequence[float]) -> Sequence[float]:
        return [scale * i for i in area]

    return func


layout = create_layout(prepare.SCALE)


class GraphicBox(Sprite):
    """
    Generic class for drawing graphical boxes.

    Draws a border and can fill in the box with a _color from the border file,
    an external file, or a solid _color.

    box = GraphicBox('border.png')
    box.draw(surface, rect)

    The border graphic must contain 9 tiles laid out in a box.
    """

    def __init__(
        self,
        border: Optional[pygame.surface.Surface] = None,
        background: Optional[pygame.surface.Surface] = None,
        color: Optional[ColorLike] = None,
        fill_tiles: bool = False,
    ) -> None:
        super().__init__()
        self._background = background
        self._color = color
        self._fill_tiles = fill_tiles
        self._tiles: List[pygame.surface.Surface] = []
        self._tile_size = 0, 0

        if border:
            self._set_border(border)

    def calc_inner_rect(self, rect: Rect) -> Rect:
        if self._tiles:
            tw, th = self._tile_size
            return rect.inflate(-tw * 2, -th * 2)
        else:
            return rect

    def _set_border(self, image: pygame.surface.Surface) -> None:
        iw, ih = image.get_size()
        tw, th = iw // 3, ih // 3
        self._tile_size = tw, th
        self._tiles = [
            image.subsurface((x, y, tw, th))
            for x, y in product(range(0, iw, tw), range(0, ih, th))
        ]

    def update_image(self) -> None:
        rect = Rect((0, 0), self._rect.size)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self._original_image = surface
        self._image = surface
        self._draw(surface, rect)

    def _draw(
        self,
        surface: pygame.surface.Surface,
        rect: Rect,
    ) -> None:
        inner = self.calc_inner_rect(rect)

        # fill center with a _background surface
        if self._background:
            surface.blit(pygame.transform.scale(self._background, inner.size), inner)

        # fill center with solid _color
        elif self._color:
            surface.fill(self._color, inner)

        # fill center with tiles from the border file
        elif self._fill_tiles:
            tw, th = self._tile_size
            p = product(range(inner.left, inner.right, tw), range(inner.top, inner.bottom, th))
            [surface.blit(self._tiles[4], pos) for pos in p]

        # draw the border
        if self._tiles:
            surface_blit = surface.blit
            tile_nw, tile_w, tile_sw, tile_n, tile_c, tile_s, tile_ne, tile_e, tile_se = self._tiles
            left, top = rect.topleft
            tw, th = self._tile_size

            # draw top and bottom tiles
            area: Optional[Tuple[int, int, int, int]]

            for x in range(inner.left, inner.right, tw):
                if x + tw >= inner.right:
                    area = 0, 0, tw - (x + tw - inner.right), th
                else:
                    area = None
                surface_blit(tile_n, (x, top), area)
                surface_blit(tile_s, (x, inner.bottom), area)

            # draw left and right tiles
            for y in range(inner.top, inner.bottom, th):
                if y + th >= inner.bottom:
                    area = 0, 0, tw, th - (y + th - inner.bottom)
                else:
                    area = None
                surface_blit(tile_w, (left, y), area)
                surface_blit(tile_e, (inner.right, y), area)

            # draw corners
            surface_blit(tile_nw, (left, top))
            surface_blit(tile_sw, (left, inner.bottom))
            surface_blit(tile_ne, (inner.right, top))
            surface_blit(tile_se, (inner.right, inner.bottom))


def guest_font_height(font: pygame.font.Font) -> int:
    return guess_rendered_text_size("Tg", font)[1]


def guess_rendered_text_size(
    text: str,
    font: pygame.font.Font,
) -> Tuple[int, int]:
    return font.size(text)


def shadow_text(
    font: pygame.font.Font,
    fg: ColorLike,
    bg: ColorLike,
    text: str,
) -> pygame.surface.Surface:
    top = font.render(text, True, fg)
    shadow = font.render(text, True, bg)

    offset = layout((0.5, 0.5))
    size = [int(math.ceil(a + b)) for a, b in zip(offset, top.get_size())]
    image = pygame.Surface(size, pygame.SRCALPHA)

    image.blit(shadow, offset)
    image.blit(top, (0, 0))
    return image


def iter_render_text(
    text: str,
    font: pygame.font.Font,
    fg: ColorLike,
    bg: ColorLike,
    rect: Rect,
) -> Generator[Tuple[Rect, pygame.surface.Surface], None, None]:
    line_height = guest_font_height(font)
    for line_index, line in enumerate(constrain_width(text, font, rect.width)):
        top = rect.top + line_index * line_height
        for scrap in build_line(line):
            if scrap[-1] == " ":
                # No need to blit a white sprite onto a white background
                continue
            dirty_length = font.size(scrap[:-1])[0]
            surface = shadow_text(font, fg, bg, scrap[-1])
            update_rect = surface.get_rect(top=top, left=rect.left + dirty_length)
            yield update_rect, surface


def build_line(text: str) -> Generator[str, None, None]:
    for index in range(1, len(text) + 1):
        yield text[:index]


def constrain_width(
    text: str,
    font: pygame.font.Font,
    width: int,
) -> Generator[str, None, None]:
    for line in iterate_word_lines(text):
        scrap = None
        for word in line:
            if scrap:
                test = scrap + " " + word
            else:
                test = word
            token_width = font.size(test)[0]
            if token_width >= width:
                if scrap is None:
                    logger.error("message is too large for width", text)
                    raise RuntimeError
                yield scrap
                scrap = word
            else:
                scrap = test
        else:  # executed when line is too large
            yield scrap if scrap else ""


def iterate_words(text: str) -> Generator[str, None, None]:
    yield from text.split(" ")


def iterate_lines(text: str) -> Generator[str, None, None]:
    yield from text.strip().split("\n")


def iterate_word_lines(text: str) -> Generator[Iterable[str], None, None]:
    for line in iterate_lines(text):
        yield iterate_words(line)


def blit_alpha(
    target: pygame.surface.Surface,
    source: pygame.surface.Surface,
    location: Tuple[int, int],
    opacity: int,
) -> None:
    """
    Blits a surface with alpha that can also have it's overall transparency modified
    Taken from http://nerdparadise.com/tech/python/pygame/blitopacity/

    NOTE: This should be removed because of the performance implications.
    """

    x = location[0]
    y = location[1]
    temp = pygame.Surface((source.get_width(), source.get_height())).convert()
    temp.blit(target, (-x, -y))
    temp.blit(source, (0, 0))
    temp.set_alpha(opacity)
    target.blit(temp, location)
