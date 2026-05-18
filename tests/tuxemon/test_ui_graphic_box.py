# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pygame
import pytest
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.ui.graphic_box import GraphicBox


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


@pytest.fixture
def surface():
    return pygame.display.get_surface()


@pytest.fixture
def border_img():
    img = Surface((30, 30))
    img.fill((255, 255, 255))
    return img


@pytest.fixture
def default_rect():
    return Rect(0, 0, 100, 100)


def test_graphicbox_init_defaults(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    assert box._background is None
    assert box._color is None
    assert box._fill_tiles is False
    assert len(box._tiles) == 9
    assert box._tile_size == (10, 10)


def test_graphicbox_set_border_valid(default_rect, border_img):
    img = Surface((12, 12))  # divisible by 3
    box = GraphicBox(default_rect, border_img)
    box._set_border(img)
    assert box._tile_size == (4, 4)
    assert len(box._tiles) == 9


def test_graphicbox_set_border_invalid_size(default_rect, border_img):
    img = Surface((10, 12))  # not divisible by 3
    box = GraphicBox(default_rect, border_img)
    with pytest.raises(ValueError):
        box._set_border(img)


def test_graphicbox_rejects_non_3x3_border(default_rect):
    img = Surface((40, 40))  # 40 % 3 != 0
    box = GraphicBox(default_rect, img)
    assert box._tiles == {}
    assert box._tile_size == (0, 0)


def test_graphicbox_border_tile_size(default_rect):
    img = Surface((30, 30))
    box = GraphicBox(default_rect, img)
    assert box._tile_size == (10, 10)


def test_graphicbox_calc_inner_rect_no_tiles(default_rect, border_img):
    rect = Rect(0, 0, 100, 100)
    box = GraphicBox(default_rect, border_img)
    box._tiles = {}
    box._tile_size = (0, 0)
    assert box.inner_rect == rect


def test_graphicbox_calc_inner_rect_with_tiles(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._tiles = {"c": Surface((10, 10))}
    box._tile_size = (10, 10)
    inner = box.inner_rect
    assert inner == Rect(10, 10, 80, 80)


def test_graphicbox_draw_no_background_or_color(
    default_rect, border_img, surface
):
    box = GraphicBox(default_rect, border_img)
    rect = Rect(0, 0, 100, 100)
    box._draw(surface, rect)  # should not crash


def test_graphicbox_draw_with_background(default_rect, border_img, surface):
    box = GraphicBox(default_rect, border_img)
    box._background = Surface((100, 100))
    rect = Rect(0, 0, 100, 100)
    box._draw(surface, rect)


def test_graphicbox_draw_with_color(default_rect, border_img, surface):
    box = GraphicBox(default_rect, border_img)
    box._color = (255, 0, 0)
    rect = Rect(0, 0, 100, 100)
    box._draw(surface, rect)


def test_graphicbox_update_image(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._rect = Rect(0, 0, 100, 100)
    box.update_image()
    assert box.image is not None


def test_tiles_are_independent_copies(default_rect):
    img = Surface((30, 30))
    img.fill((10, 10, 10))
    box = GraphicBox(default_rect, img)
    img.fill((200, 0, 0))  # mutate original
    assert box._tiles["c"].get_at((0, 0)) == (10, 10, 10, 255)


def test_border_clipping_no_crash_and_no_overlap(default_rect, surface):
    img = Surface((30, 30))
    img.fill((255, 255, 255))
    box = GraphicBox(default_rect, img)
    rect = Rect(0, 0, 37, 37)
    box._draw(surface, rect)


def test_corner_tiles_positions(default_rect):
    img = Surface((30, 30))
    box = GraphicBox(default_rect, img)
    rect = Rect(0, 0, 30, 30)
    surf = Surface(rect.size)
    box._draw(surf, rect)
    assert surf.get_at((0, 0)) is not None
    assert surf.get_at((29, 0)) is not None
    assert surf.get_at((0, 29)) is not None
    assert surf.get_at((29, 29)) is not None


def test_update_image_requires_rect(border_img):
    with pytest.raises(ValueError):
        GraphicBox(Rect(0, 0, 0, 0), border_img)


def test_fill_priority_background_over_color(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._background = Surface((10, 10))
    box._color = (255, 0, 0)
    box._fill_tiles = True
    surf = Surface((100, 100))
    box._draw(surf, default_rect)
    assert surf.get_at((50, 50)) == box._background.get_at((0, 0))


def test_fill_priority_color_over_tiles(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._background = None
    box._color = (123, 45, 67)
    box._fill_tiles = True
    surf = Surface((100, 100))
    box._draw(surf, default_rect)
    assert surf.get_at((50, 50)) == (123, 45, 67, 255)


def test_set_color_resets_background_and_tiles(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._background = Surface((10, 10))
    box._fill_tiles = True
    box.set_color((10, 20, 30))
    assert box._background is None
    assert box._fill_tiles is False
    assert box._color == (10, 20, 30)
    assert box._needs_update is True


def test_set_border_sets_needs_update(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._needs_update = False
    new_img = Surface((30, 30))
    box.set_border(new_img)
    assert box._needs_update is True


def test_tiled_fill_repeats_tiles(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._tiles = {"c": Surface((10, 10))}
    box._tile_size = (10, 10)
    box._fill_tiles = True
    surf = Surface((40, 40))
    inner = Rect(10, 10, 20, 20)
    box._draw_tiled_fill(surf, inner)
    assert surf.get_at((10, 10)) == (0, 0, 0, 255)
    assert surf.get_at((19, 10)) == (0, 0, 0, 255)
    assert surf.get_at((10, 19)) == (0, 0, 0, 255)
    assert surf.get_at((19, 19)) == (0, 0, 0, 255)


def test_border_edges_drawn(default_rect):
    img = Surface((30, 30))
    img.fill((255, 255, 255))
    box = GraphicBox(default_rect, img)
    rect = Rect(0, 0, 40, 40)
    surf = Surface(rect.size)
    box._draw(surf, rect)
    assert surf.get_at((15, 0)) != (0, 0, 0, 255)
    assert surf.get_at((15, 39)) != (0, 0, 0, 255)
    assert surf.get_at((0, 15)) != (0, 0, 0, 255)
    assert surf.get_at((39, 15)) != (0, 0, 0, 255)


def test_inner_rect_never_negative(default_rect, border_img):
    box = GraphicBox(Rect(0, 0, 10, 10), border_img)
    inner = box.inner_rect
    assert inner.width >= 0
    assert inner.height >= 0


def test_update_image_draws_content(default_rect, border_img):
    box = GraphicBox(default_rect, border_img)
    box._color = (50, 100, 150)
    box.update_image()
    surf = box.image
    assert surf.get_at((50, 50)) == (50, 100, 150, 255)
    assert surf.get_at((0, 0)) != (50, 100, 150, 255)
