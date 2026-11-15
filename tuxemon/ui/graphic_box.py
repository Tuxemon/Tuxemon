# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from pygame import SRCALPHA, draw
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.transform import scale

from tuxemon.graphics import ColorLike
from tuxemon.sprite import Sprite
from tuxemon.ui.tile_layout import NineSliceLayout

DEBUG_NINESLICE = False


class GraphicBox(Sprite):
    """
    A rect-driven nine-slice UI container.

    GraphicBox renders a scalable box using a 3x3 nine-slice border image.
    The widget fills its inner area using one of three modes:

        • a solid color
        • a scaled background surface
        • a tiled center slice from the border image

    The border image must be divisible into a 3x3 grid of equal tiles.
    Rendering is rect-driven: the widget draws itself into the rectangle
    defined by its assigned rect, and all scaling/clipping is derived from it.

    Example:
        box = GraphicBox(rect, border_surface)
        box.draw(surface, rect)
    """

    def __init__(
        self,
        rect: Rect,
        border: Surface,
        background: Surface | None = None,
        color: ColorLike | None = None,
        fill_tiles: bool = False,
    ) -> None:
        super().__init__()

        if rect.width <= 0 or rect.height <= 0:
            raise ValueError("GraphicBox requires a non-zero rect.")

        self._rect = rect.copy()
        self._background = background
        self._color = color
        self._fill_tiles = fill_tiles

        self._tiles: dict[str, Surface] = {}
        self._tile_size: tuple[int, int] = (0, 0)

        if border is not None:
            w, h = border.get_width(), border.get_height()
            if w % 3 == 0 and h % 3 == 0:
                self.set_border(border)
            else:
                self._tiles = {}
                self._tile_size = (0, 0)

        self._needs_update = True

    @property
    def inner_rect(self) -> Rect:
        return self.calc_inner_rect(self._rect)

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
            inner = rect.inflate(-tw * 2, -th * 2)

            if inner.width < 0 or inner.height < 0:
                inner.width = max(inner.width, 0)
                inner.height = max(inner.height, 0)

            return inner

        return rect

    def set_color(self, color: ColorLike | None) -> None:
        """
        Change the fill color at runtime.
        Passing None disables color fill.
        """
        self._color = color

        if color is not None:
            self._background = None
            self._fill_tiles = False

        self._needs_update = True

    def set_border(self, image: Surface) -> None:
        """
        Public method to change the border at runtime.
        Re-slices the image using the configured layout class.
        """
        self._set_border(image)
        self._needs_update = True

    def _set_border(self, image: Surface) -> None:
        """
        Sets the border image and extracts the individual tiles.
        The border graphic must contain 9 tiles laid out in a 3x3 grid.

        Parameters:
            image: The border image.
        """
        layout = NineSliceLayout(image)
        self._tiles = layout.tiles
        self._tile_size = layout.tile_size

    def update_image(self, source: Surface | None = None) -> None:
        """
        Updates the object's image by drawing the box on a new surface.
        """
        if not hasattr(self, "_rect") or self._rect.size == (0, 0):
            raise RuntimeError(
                "GraphicBox._rect must be set to a non-zero size before update_image()"
            )

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
        blit = self._blit_clipped

        # Top + bottom
        for x in range(inner.left, inner.right, tw):
            remaining = inner.right - x
            blit(surface, self._tiles["n"], (x, top), remaining, th)
            blit(surface, self._tiles["s"], (x, inner.bottom), remaining, th)

        # Left + right
        for y in range(inner.top, inner.bottom, th):
            remaining = inner.bottom - y
            blit(surface, self._tiles["w"], (left, y), tw, remaining)
            blit(surface, self._tiles["e"], (inner.right, y), tw, remaining)

        # Corners (no clipping needed)
        surface.blit(self._tiles["nw"], (left, top))
        surface.blit(self._tiles["sw"], (left, inner.bottom))
        surface.blit(self._tiles["ne"], (inner.right, top))
        surface.blit(self._tiles["se"], (inner.right, inner.bottom))

        if DEBUG_NINESLICE:
            draw.rect(surface, (255, 0, 0), (x, top, remaining, th), 1)

    def _blit_clipped(
        self,
        surface: Surface,
        tile: Surface,
        dest: tuple[int, int],
        max_w: int,
        max_h: int,
    ) -> None:
        area = (
            0,
            0,
            min(tile.get_width(), max_w),
            min(tile.get_height(), max_h),
        )
        surface.blit(tile, dest, area)
