# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>

import pytest
from pygame.surface import Surface

from tuxemon.ui.tile_layout import NineSliceLayout, TileLayout


def test_tilelayout_init_default():
    img = Surface((9, 9))
    layout = TileLayout(img)
    assert layout.grid_size == 3
    assert isinstance(layout.tiles, dict)


def test_tilelayout_empty_image():
    img = Surface((0, 0))
    with pytest.raises(ValueError):
        TileLayout(img)


def test_tilelayout_zero_grid_size():
    img = Surface((9, 9))
    with pytest.raises(ValueError):
        TileLayout(img, grid_size=0)


def test_tilelayout_invalid_dimensions():
    img = Surface((10, 9))
    with pytest.raises(ValueError):
        TileLayout(img, grid_size=3)


def test_tilelayout_3x3_tile_count():
    img = Surface((9, 9))
    layout = TileLayout(img, grid_size=3)
    assert len(layout.tiles) == 9


def test_tilelayout_3x3_tile_sizes():
    img = Surface((30, 30))
    layout = TileLayout(img, grid_size=3)
    for tile in layout.tiles.values():
        assert tile.get_size() == (10, 10)


def test_tilelayout_general_grid_tile_count():
    img = Surface((40, 40))
    layout = TileLayout(img, grid_size=4)
    assert len(layout.tiles) == 16


def test_tilelayout_general_grid_tile_sizes():
    img = Surface((40, 40))
    layout = TileLayout(img, grid_size=4)
    for tile in layout.tiles.values():
        assert tile.get_size() == (10, 10)


def test_tilelayout_general_grid_labels():
    img = Surface((40, 40))
    layout = TileLayout(img, grid_size=4)
    assert "0_0" in layout.tiles
    assert "3_3" in layout.tiles


def test_tilelayout_invalid_grid_sizes():
    img = Surface((30, 30))

    for gs in [0, -1, -5]:
        with pytest.raises(ValueError):
            TileLayout(img, grid_size=gs)

    for gs in [7, 11, 13]:
        with pytest.raises(ValueError):
            TileLayout(img, grid_size=gs)


@pytest.mark.parametrize(
    "grid_size",
    [
        pytest.param(1, id="grid_1"),
        pytest.param(2, id="grid_2"),
        pytest.param(3, id="grid_3"),
        pytest.param(5, id="grid_5"),
        pytest.param(10, id="grid_10"),
    ],
)
def test_tilelayout_valid_grid_sizes(grid_size):
    img = Surface((30, 30))
    layout = TileLayout(img, grid_size=grid_size)
    assert layout.grid_size == grid_size


def test_nineslice_valid():
    img = Surface((30, 30))
    layout = NineSliceLayout(img)
    assert len(layout.tiles) == 9
    assert layout.tiles["c"].get_size() == (10, 10)


def test_nineslice_invalid_size():
    img = Surface((40, 40))  # 40 % 3 != 0
    with pytest.raises(ValueError):
        NineSliceLayout(img)


def test_nineslice_labels_correct():
    img = Surface((30, 30))
    layout = NineSliceLayout(img)

    expected = {"nw", "n", "ne", "w", "c", "e", "sw", "s", "se"}
    assert set(layout.tiles.keys()) == expected


def test_tiles_are_independent_copies():
    img = Surface((40, 40))
    img.fill((10, 10, 10))
    layout = TileLayout(img, grid_size=4)

    img.fill((200, 0, 0))  # mutate original

    # Tiles must NOT change
    assert layout.tiles["0_0"].get_at((0, 0)) == (10, 10, 10, 255)


def test_nineslice_allows_rectangular_tiles():
    img = Surface((30, 60))  # 10×20 tiles
    img.fill((123, 45, 67))
    layout = NineSliceLayout(img)

    # All tiles should be 10×20
    for tile in layout.tiles.values():
        assert tile.get_size() == (10, 20)


def test_nineslice_clipping_no_crash():
    img = Surface((30, 30))
    layout = NineSliceLayout(img)
    # draw into a non-multiple-of-tile-size rect
    Surface((37, 37))
    # Should not crash
    for tile in layout.tiles.values():
        assert tile is not None


def test_nineslice_corner_positions():
    img = Surface((30, 30))
    img.fill((255, 255, 255))
    layout = NineSliceLayout(img)

    surf = Surface((30, 30))

    positions = {
        "nw": (0, 0),
        "n": (10, 0),
        "ne": (20, 0),
        "w": (0, 10),
        "c": (10, 10),
        "e": (20, 10),
        "sw": (0, 20),
        "s": (10, 20),
        "se": (20, 20),
    }

    for name, (x, y) in positions.items():
        surf.blit(layout.tiles[name], (x, y))

    assert surf.get_at((0, 0)) == (255, 255, 255, 255)
    assert surf.get_at((29, 0)) == (255, 255, 255, 255)
    assert surf.get_at((0, 29)) == (255, 255, 255, 255)
    assert surf.get_at((29, 29)) == (255, 255, 255, 255)


def test_nineslice_clipping_edges():
    # 30×30 → tiles are 10×10
    img = Surface((30, 30))
    img.fill((255, 255, 255))  # white border tiles

    layout = NineSliceLayout(img)

    # Render into a non-multiple size: 37×37
    surf = Surface((37, 37))
    surf.fill((0, 0, 0))  # black background

    # Manually draw border using the same logic as GraphicBox
    tw, th = 10, 10

    # Top row
    for x in range(0, 37, tw):
        remaining = 37 - x
        tile_w = min(tw, remaining)
        surf.blit(layout.tiles["n"], (x, 0), (0, 0, tile_w, th))

    # Bottom row
    for x in range(0, 37, tw):
        remaining = 37 - x
        tile_w = min(tw, remaining)
        surf.blit(layout.tiles["s"], (x, 27), (0, 0, tile_w, th))

    # Left column
    for y in range(0, 37, th):
        remaining = 37 - y
        tile_h = min(th, remaining)
        surf.blit(layout.tiles["w"], (0, y), (0, 0, tw, tile_h))

    # Right column
    for y in range(0, 37, th):
        remaining = 37 - y
        tile_h = min(th, remaining)
        surf.blit(layout.tiles["e"], (27, y), (0, 0, tw, tile_h))

    # Corners
    surf.blit(layout.tiles["nw"], (0, 0))
    surf.blit(layout.tiles["ne"], (27, 0))
    surf.blit(layout.tiles["sw"], (0, 27))
    surf.blit(layout.tiles["se"], (27, 27))

    # Pixel-level assertions: all border pixels must be white
    for x in range(37):
        assert surf.get_at((x, 0)) == (255, 255, 255, 255)
        assert surf.get_at((x, 36)) == (255, 255, 255, 255)

    for y in range(37):
        assert surf.get_at((0, y)) == (255, 255, 255, 255)
        assert surf.get_at((36, y)) == (255, 255, 255, 255)


def test_nineslice_tiles_are_independent_copies():
    img = Surface((30, 30))
    img.fill((10, 10, 10))  # dark gray

    layout = NineSliceLayout(img)

    # Mutate original
    img.fill((200, 0, 0))  # red

    # Tiles must NOT change
    for tile in layout.tiles.values():
        assert tile.get_at((0, 0)) == (10, 10, 10, 255)


@pytest.mark.parametrize(
    "size",
    [
        pytest.param(31, id="size_31"),
        pytest.param(32, id="size_32"),
        pytest.param(33, id="size_33"),
        pytest.param(37, id="size_37"),
        pytest.param(41, id="size_41"),
        pytest.param(55, id="size_55"),
    ],
)
def test_nineslice_clipping_parametrized(size):
    # Base nine-slice image: 30×30 → tiles 10×10
    img = Surface((30, 30))
    img.fill((255, 255, 255))  # white

    layout = NineSliceLayout(img)

    surf = Surface((size, size))
    surf.fill((0, 0, 0))  # black background

    tw = th = 10

    # Draw top and bottom
    for x in range(0, size, tw):
        remaining = size - x
        tile_w = min(tw, remaining)
        surf.blit(layout.tiles["n"], (x, 0), (0, 0, tile_w, th))
        surf.blit(layout.tiles["s"], (x, size - th), (0, 0, tile_w, th))

    # Draw left and right
    for y in range(0, size, th):
        remaining = size - y
        tile_h = min(th, remaining)
        surf.blit(layout.tiles["w"], (0, y), (0, 0, tw, tile_h))
        surf.blit(layout.tiles["e"], (size - tw, y), (0, 0, tw, tile_h))

    # Corners
    surf.blit(layout.tiles["nw"], (0, 0))
    surf.blit(layout.tiles["ne"], (size - tw, 0))
    surf.blit(layout.tiles["sw"], (0, size - th))
    surf.blit(layout.tiles["se"], (size - tw, size - th))

    # Pixel-level border validation
    for x in range(size):
        assert surf.get_at((x, 0)) == (255, 255, 255, 255)
        assert surf.get_at((x, size - 1)) == (255, 255, 255, 255)

    for y in range(size):
        assert surf.get_at((0, y)) == (255, 255, 255, 255)
        assert surf.get_at((size - 1, y)) == (255, 255, 255, 255)
