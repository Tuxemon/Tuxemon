# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

from pygame import SRCALPHA
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.transform import scale

from tuxemon.graphics import ColorLike
from tuxemon.sprite import Sprite


class TileLayout:
    """
    Extracts a grid of tiles from a border image and assigns logical names
    like 'nw', 'n', 'ne', etc. Assumes a 3x3 layout by default.
    """

    def __init__(self, image: Surface, grid_size: int = 3) -> None:
        if grid_size <= 0:
            raise ValueError("Grid size must be a positive integer")
        self.grid_size = grid_size
        self.tiles: dict[str, Surface] = self._extract_tiles(image)

    def _extract_tiles(self, image: Surface) -> dict[str, Surface]:
        if image.get_size() == (0, 0):
            raise ValueError("Image cannot be empty")

        iw, ih = image.get_size()

        if iw % self.grid_size != 0 or ih % self.grid_size != 0:
            raise ValueError("Image dimensions must be divisible by grid size")

        tw, th = iw // self.grid_size, ih // self.grid_size
        layout_map = {
            (0, 0): "nw",
            (0, 1): "n",
            (0, 2): "ne",
            (1, 0): "w",
            (1, 1): "c",
            (1, 2): "e",
            (2, 0): "sw",
            (2, 1): "s",
            (2, 2): "se",
        }

        tiles: dict[str, Surface] = {}
        for (row, col), label in layout_map.items():
            x, y = col * tw, row * th
            rect = Rect(x, y, tw, th)
            tiles[label] = image.subsurface(rect)

        if len(tiles) != self.grid_size**2:
            raise ValueError(
                f"Expected {self.grid_size ** 2} tiles, got {len(tiles)}"
            )

        return tiles


class GraphicBox(Sprite):
    """
    Generic class for drawing graphical boxes.

    Draws a border and can fill in the box with a _color from the border file,
    an external file, or a solid _color.

    box = GraphicBox('border.png')
    box.draw(surface, rect)

    The border graphic must contain 9 tiles laid out in a box.
    """

    TILE_GRID_SIZE = 3

    def __init__(
        self,
        border: Optional[Surface] = None,
        background: Optional[Surface] = None,
        color: Optional[ColorLike] = None,
        fill_tiles: bool = False,
    ) -> None:
        """
        Initializes the GraphicBox object.

        Parameters:
            border: The border image.
            background: The background image.
            color: The fill color.
            fill_tiles: Whether to fill the box with tiles from the border image.
        """
        super().__init__()
        self._background = background
        self._color = color
        self._fill_tiles = fill_tiles
        self._tiles: dict[str, Surface] = {}
        self._tile_size = 0, 0

        if border:
            self._set_border(border)

    def calc_inner_rect(self, rect: Rect) -> Rect:
        """
        Calculates the inner rectangle of the box.

        Parameters:
            rect: The outer rectangle of the box.

        Returns:
            The inner rectangle of the box.
        """
        if self._tiles:
            tw, th = self._tile_size
            return rect.inflate(-tw * 2, -th * 2)
        else:
            return rect

    def _set_border(self, image: Surface) -> None:
        """
        Sets the border image and extracts the individual tiles.
        The border graphic must contain 9 tiles laid out in a 3x3 grid.

        Parameters:
            image: The border image.
        """
        layout = TileLayout(image, self.TILE_GRID_SIZE)
        self._tiles = layout.tiles
        self._tile_size = next(iter(self._tiles.values())).get_size()
        self._needs_update = True

    def update_image(self) -> None:
        """
        Updates the object's image by drawing the box on a new surface.
        """
        rect = Rect((0, 0), self._rect.size)
        surface = Surface(rect.size, SRCALPHA)
        self._draw(surface, rect)
        self.image = surface

    def _draw(
        self,
        surface: Surface,
        rect: Rect,
    ) -> Rect:
        inner = self.calc_inner_rect(rect)

        # Fill center
        if self._background:
            surface.blit(scale(self._background, inner.size), inner)
        elif self._color:
            surface.fill(self._color, inner)
        elif self._fill_tiles:
            self._draw_tiled_fill(surface, inner)

        # Draw border
        if self._tiles:
            self._draw_border(surface, rect, inner)

        return rect

    def _draw_tiled_fill(self, surface: Surface, inner: Rect) -> None:
        tw, th = self._tile_size
        center_tile = self._tiles["c"]
        for x in range(inner.left, inner.right, tw):
            for y in range(inner.top, inner.bottom, th):
                surface.blit(center_tile, (x, y))

    def _draw_border(self, surface: Surface, rect: Rect, inner: Rect) -> None:
        """
        Draws the tiled border around the inner rectangle.
        """
        left, top = rect.topleft
        tw, th = self._tile_size
        surface_blit = surface.blit  # cache the blit method

        # Draw top and bottom border tiles
        for x in range(inner.left, inner.right, tw):
            area = (
                (0, 0, tw, th)
                if x + tw < inner.right
                else (0, 0, tw - (x + tw - inner.right), th)
            )
            surface_blit(self._tiles["n"], (x, top), area)
            surface_blit(self._tiles["s"], (x, inner.bottom), area)

        # Draw left and right border tiles
        for y in range(inner.top, inner.bottom, th):
            area = (
                (0, 0, tw, th)
                if y + th < inner.bottom
                else (0, 0, tw, th - (y + th - inner.bottom))
            )
            surface_blit(self._tiles["w"], (left, y), area)
            surface_blit(self._tiles["e"], (inner.right, y), area)

        # Draw corner tiles
        surface_blit(self._tiles["nw"], (left, top))
        surface_blit(self._tiles["sw"], (left, inner.bottom))
        surface_blit(self._tiles["ne"], (inner.right, top))
        surface_blit(self._tiles["se"], (inner.right, inner.bottom))
