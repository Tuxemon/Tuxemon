from __future__ import division

import math
import logging
from itertools import product

import pygame

from core import prepare
from core.components.sprite import Sprite

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

__all__ = ('GraphicBox', 'draw_text')


def layout(scale):
    def func(area):
        return [scale * i for i in area]

    return func


layout = layout(prepare.SCALE)


class GraphicBox(Sprite):
    """ Generic class for drawing graphical boxes

    Draws a border and can fill in the box with a _color from the border file,
    an external file, or a solid _color.

    box = GraphicBox('border.png')
    box.draw(surface, rect)

    The border graphic must contain 9 tiles laid out in a box.
    """
    def __init__(self, border=None, background=None, color=None, fill_tiles=False):
        super(GraphicBox, self).__init__()
        self._background = background
        self._color = color
        self._fill_tiles = fill_tiles
        self._tiles = list()
        self._tile_size = 0, 0
        self._rect = None
        if border:
            self._set_border(border)

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect):
        if not rect == self._rect:
            self._rect = rect
            self._needs_update = True

    def calc_inner_rect(self, rect):
        if self._tiles:
            tw, th = self._tile_size
            return rect.inflate(- tw * 2, -th * 2)
        else:
            return rect

    def _set_border(self, image):
        iw, ih = image.get_size()
        tw, th = iw // 3, ih // 3
        self._tile_size = tw, th
        self._tiles = [image.subsurface((x, y, tw, th))
                       for x, y in product(range(0, iw, tw), range(0, ih, th))]

    def update_image(self):
        rect = pygame.Rect((0, 0), self._rect.size)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        self._original_image = surface
        self._image = surface
        self._draw(surface, rect)

    def _draw(self, surface, rect):
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
            p = product(range(inner.left, inner.right, tw),
                        range(inner.top, inner.bottom, th))
            [surface.blit(self._tiles[4], pos) for pos in p]

        # draw the border
        if self._tiles:
            surface_blit = surface.blit
            tile_nw, tile_w, tile_sw, tile_n, tile_c, tile_s, tile_ne, tile_e, tile_se = self._tiles
            left, top = rect.topleft
            tw, th = self._tile_size

            # draw top and bottom tiles
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


def guest_font_height(font):
    return guess_rendered_text_size("Tg", font)[1]


def guess_rendered_text_size(text, font):
    return font.size(text)


def shadow_text(font, fg, bg, text):
    top = font.render(text, 1, fg)
    shadow = font.render(text, 1, bg)

    offset = layout((0.5, 0.5))
    size = [int(math.ceil(a + b)) for a, b in zip(offset, top.get_size())]
    image = pygame.Surface(size, pygame.SRCALPHA)

    image.blit(shadow, offset)
    image.blit(top, (0, 0))
    return image


def iter_render_text(text, font, fg, bg, rect):
    line_height = guest_font_height(font)
    dirty = rect
    for line_index, line in enumerate(constrain_width(text, font, rect.width)):
        top = rect.top + line_index * line_height
        for scrap in build_line(line):
            surface = shadow_text(font, fg, bg, scrap)
            update_rect = surface.get_rect(top=top, left=rect.left)
            yield dirty, update_rect, surface
            dirty = update_rect
        dirty = (0, 0, 0, 0)


def build_line(text):
    for index in range(1, len(text) + 1):
        yield text[:index]


def constrain_width(text, font, width):
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
                    print('message is too large for width', text)
                    raise RuntimeError
                yield scrap
                scrap = word
            else:
                scrap = test
        else:  # executed when line is too large
            yield scrap


def iterate_words(text):
    for word in text.split(" "):
        yield word


def iterate_lines(text):
    for line in text.strip().split("\n"):
        yield line


def iterate_word_lines(text):
    for line in iterate_lines(text):
        yield iterate_words(line)
