# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from pygame.rect import Rect
from pygame.surface import Surface


class TileLayout:
    """
    Extracts a grid of tiles from an image. For grid_size=3, semantic labels
    (nw, n, ne, w, c, e, sw, s, se) are used. Otherwise row_col labels.
    """

    def __init__(self, image: Surface, grid_size: int = 3) -> None:
        if grid_size <= 0:
            raise ValueError("Grid size must be a positive integer")
        self.grid_size = grid_size
        self.tiles: dict[str, Surface] = self._extract_tiles(image)

    @property
    def tile_size(self) -> tuple[int, int]:
        first = next(iter(self.tiles.values()))
        return first.get_width(), first.get_height()

    def _extract_tiles(self, image: Surface) -> dict[str, Surface]:
        iw, ih = image.get_size()

        if iw == 0 or ih == 0:
            raise ValueError("Image cannot be empty")

        if iw % self.grid_size != 0 or ih % self.grid_size != 0:
            raise ValueError("Image dimensions must be divisible by grid size")

        if iw // self.grid_size == 0 or ih // self.grid_size == 0:
            raise ValueError("Grid size too large for image dimensions")

        tw, th = iw // self.grid_size, ih // self.grid_size

        # Label selection
        if self.grid_size == 3:
            labels = {
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
        else:
            labels = self._generate_default_labels()

        # Slice tiles
        tiles = {}
        for (row, col), label in labels.items():
            rect = Rect(col * tw, row * th, tw, th)
            tiles[label] = image.subsurface(rect).copy()

        return tiles

    def _generate_default_labels(self) -> dict[tuple[int, int], str]:
        return {
            (row, col): f"{row}_{col}"
            for row in range(self.grid_size)
            for col in range(self.grid_size)
        }

    def __repr__(self) -> str:
        return f"<TileLayout grid={self.grid_size} tiles={list(self.tiles.keys())}>"


class NineSliceLayout(TileLayout):
    """
    Strict 3x3 nine-slice layout used by GraphicBox.
    """

    NINE_SLICE_MAP = {
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

    def __init__(self, image: Surface):
        super().__init__(image, grid_size=3)

    def _extract_tiles(self, image: Surface) -> dict[str, Surface]:
        iw, ih = image.get_size()

        if iw % 3 != 0 or ih % 3 != 0:
            raise ValueError("Image must be divisible by 3 for nine-slice")

        tw, th = iw // 3, ih // 3

        tiles = {}
        for (row, col), label in self.NINE_SLICE_MAP.items():
            rect = Rect(col * tw, row * th, tw, th)
            tiles[label] = image.subsurface(rect).copy()

        # Contributor-proofing check
        required = set(self.NINE_SLICE_MAP.values())
        missing = required - tiles.keys()
        if missing:
            raise ValueError(f"Border image missing tiles: {missing}")

        return tiles
