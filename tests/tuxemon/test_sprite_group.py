# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pygame
import pytest
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.menu.grid_index_model import GridIndexModel
from tuxemon.platform.const import buttons
from tuxemon.sprite import (
    MenuSpriteGroup,
    RelativeGroup,
    Sprite,
    SpriteGroup,
    VisualSpriteList,
)


class FakeSprite(Sprite):
    def __init__(self, w=10, h=10, enabled=True):
        super().__init__()
        self.image = Surface((w, h))
        self.rect = self.image.get_rect()
        self.enabled = enabled


def make_list(n):
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    lst = VisualSpriteList(parent=parent)
    for _ in range(n):
        lst.add(FakeSprite())
    return lst


def make_list_snap(enabled_flags, page_size, current_page):
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    lst = VisualSpriteList(parent=parent)
    lst.page_size = page_size
    lst.current_page = current_page

    for flag in enabled_flags:
        lst.add(FakeSprite(enabled=flag))

    return lst


def test_spritegroup_indexing_and_slicing():
    g = SpriteGroup()
    s1, s2, s3 = FakeSprite(), FakeSprite(), FakeSprite()
    g.add(s1, s2, s3)

    assert g[0] is s1
    assert g[1] is s2
    assert g[-1] is s3
    assert g[0:2] == [s1, s2]


def test_spritegroup_bool():
    g = SpriteGroup()
    assert not g
    g.add(FakeSprite())
    assert g


def test_spritegroup_bounding_rect_single():
    s = FakeSprite()
    s.rect.topleft = (50, 80)
    g = SpriteGroup()
    g.add(s)

    r = g.calc_bounding_rect()
    assert r.topleft == (50, 80)
    assert r.size == s.rect.size


def test_spritegroup_bounding_rect_multiple():
    s1 = FakeSprite()
    s2 = FakeSprite()
    s1.rect.topleft = (0, 0)
    s2.rect.topleft = (100, 50)

    g = SpriteGroup()
    g.add(s1, s2)

    r = g.calc_bounding_rect()
    assert r.left == 0
    assert r.top == 0
    assert r.right == 110
    assert r.bottom == 60


def test_spritegroup_swap():
    g = SpriteGroup()
    s1, s2 = FakeSprite(), FakeSprite()
    g.add(s1)

    g.swap(s1, s2)
    assert s1 not in g.sprites()
    assert s2 in g.sprites()


@pytest.mark.parametrize(
    "button, expected",
    [
        pytest.param("LEFT", -1, id="left-move"),
        pytest.param("RIGHT", 1, id="right-move"),
        pytest.param("UP", -1, id="up-move"),
        pytest.param("DOWN", 1, id="down-move"),
    ],
)
def test_menuspritegroup_simple_movement(button, expected):

    class E:
        pass

    E.button = getattr(pygame, "K_" + button.lower(), 0)
    E.pressed = True

    g = MenuSpriteGroup()
    for _ in range(5):
        g.add(FakeSprite())

    g._simple_movement_dict = {E.button: expected}

    new_index = g.determine_cursor_movement(2, E)
    assert new_index == (2 + expected) % 5


def test_menuspritegroup_skips_disabled_items():
    class E:
        pass

    E.button = 1
    E.pressed = True

    g = MenuSpriteGroup()
    s1 = FakeSprite(enabled=True)
    s2 = FakeSprite(enabled=False)
    s3 = FakeSprite(enabled=True)

    g.add(s1, s2, s3)
    g._simple_movement_dict = {1: 1}

    assert g.determine_cursor_movement(0, E) == 2


def test_relativegroup_draw_moves_sprites_temporarily():
    parent = RelativeGroup(parent=lambda: Rect(100, 200, 300, 300))
    g = RelativeGroup(parent=parent)
    s = FakeSprite()
    g.add(s)

    original_pos = s.rect.topleft
    g.draw(Surface((800, 600)))

    assert s.rect.topleft == original_pos


def test_relativegroup_updates_rect_from_parent_callable():
    g = RelativeGroup(parent=lambda: Rect(10, 20, 100, 100))
    g.update_rect_from_parent()
    assert g.rect.topleft == (10, 20)


def test_visualsprite_columns_auto_adjust():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    v = VisualSpriteList(parent=parent)
    v.max_width_per_column = 100

    for _ in range(5):
        v.add(FakeSprite(w=50))

    v.arrange_menu_items()
    assert v.columns == 1

    parent.update_rect_from_parent()
    v.arrange_menu_items()
    assert v.columns == 3  # 300 // 100


def test_visualsprite_advance_input_wraparound():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.columns = 3

    for _ in range(7):
        v.add(FakeSprite())

    v._2d_movement_dict = {99: ("tb", 1)}

    assert v._advance_input(6, 99) == 1


def test_empty_group_bounding_rect_safe():
    g = SpriteGroup()
    with pytest.raises(IndexError):
        g.calc_bounding_rect()


def test_empty_menu_movement_returns_zero():
    class E:
        pass

    E.button = 1
    E.pressed = True

    g = MenuSpriteGroup()
    assert g.determine_cursor_movement(0, E) == 0


def test_visualsprite_requires_parent_rect_before_arrange():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 200))
    v = VisualSpriteList(parent=parent)
    v.max_width_per_column = 100

    for _ in range(5):
        v.add(FakeSprite())

    v.arrange_menu_items()
    assert v.columns == 1


def test_visualsprite_parent_rect_propagation_explicit():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 200))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.max_width_per_column = 100

    for _ in range(5):
        v.add(FakeSprite())

    v.arrange_menu_items()
    assert v.columns == 3  # 300 // 100


def test_visualsprite_needs_arrange_lifecycle():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 200))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    assert v._needs_arrange is False

    v.add(FakeSprite())
    assert v._needs_arrange is True

    v.arrange_menu_items()
    assert v._needs_arrange is False

    v.remove(v.sprites()[0])
    assert v._needs_arrange is True


def test_visualsprite_down_movement_ragged_grid():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.columns = 3

    for _ in range(7):
        v.add(FakeSprite())

    v._2d_movement_dict = {99: ("tb", 1)}

    # Expected behavior: LR 6 → TB 2 → TB 3 → LR 1
    assert v._advance_input(6, 99) == 1


def test_visualsprite_layout_stable_after_arrange():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    for _ in range(6):
        v.add(FakeSprite())

    v.arrange_menu_items()
    first_positions = [s.rect.topleft for s in v.sprites()]

    v.arrange_menu_items()
    second_positions = [s.rect.topleft for s in v.sprites()]

    assert first_positions == second_positions


def test_visualsprite_draw_restores_rects():
    parent = RelativeGroup(parent=lambda: Rect(100, 200, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    s = FakeSprite()
    v.add(s)

    original = s.rect.topleft
    v.draw(Surface((800, 600)))
    assert s.rect.topleft == original


def test_visualsprite_vertical_orientation_layout():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.orientation = "vertical"
    v.columns = 2

    for _ in range(4):
        v.add(FakeSprite(w=20, h=20))

    v.arrange_menu_items()

    # In vertical mode:
    # index → (row, col) = divmod(index, rows)
    # so items should move horizontally first
    xs = [s.rect.x for s in v.sprites()]
    assert xs == sorted(xs)


def test_visualsprite_vertical_movement():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.orientation = "vertical"
    v.columns = 2

    for _ in range(6):
        v.add(FakeSprite())

    v._2d_movement_dict = {99: ("lr", 1)}

    # In vertical mode, LR becomes TB
    # So moving from index 0 should go to index 1
    assert v._advance_input(0, 99) == 1


def test_visualsprite_rectangular_movement_wraparound():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.rectangular = True
    v.columns = 3

    for _ in range(7):
        v.add(FakeSprite())

    v._2d_movement_dict = {99: ("tb", 1)}

    # Rectangular grid:
    # 0 1 2
    # 3 4 5
    # 6 7 8 (virtual)
    # DOWN from 6 → 7
    assert v._advance_input(6, 99) == 7 % len(v)


def test_visualsprite_rectangular_layout_stable():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.rectangular = True
    v.columns = 3

    for _ in range(5):
        v.add(FakeSprite())

    v.arrange_menu_items()
    first = [s.rect.topleft for s in v.sprites()]

    v.arrange_menu_items()
    second = [s.rect.topleft for s in v.sprites()]

    assert first == second


def test_visualsprite_add_sets_needs_arrange():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    assert v._needs_arrange is False

    s1 = FakeSprite()
    v.add(s1)
    assert v._needs_arrange is True
    assert v.sprites() == [s1]

    v.arrange_menu_items()
    assert v._needs_arrange is False

    s2 = FakeSprite()
    v.add(s2)
    assert v._needs_arrange is True
    assert v.sprites() == [s1, s2]


def test_visualsprite_clear_items_removes_all_and_sets_flag():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    for _ in range(5):
        v.add(FakeSprite())

    assert len(v) == 5
    assert v._needs_arrange is True

    v.arrange_menu_items()
    assert v._needs_arrange is False

    v.clear_items()
    assert len(v) == 0
    assert v._needs_arrange is True


def test_visualsprite_clear_items_then_readd():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    for _ in range(3):
        v.add(FakeSprite())

    v.arrange_menu_items()
    first_positions = [s.rect.topleft for s in v.sprites()]

    v.clear_items()
    for _ in range(3):
        v.add(FakeSprite())

    v.arrange_menu_items()
    second_positions = [s.rect.topleft for s in v.sprites()]

    assert first_positions == second_positions


def test_visualsprite_clear_items_safe_on_empty():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    assert len(v) == 0

    v.clear_items()
    assert len(v) == 0
    assert v._needs_arrange is True


def test_visualsprite_clear_items_uses_empty(monkeypatch):
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    for _ in range(3):
        v.add(FakeSprite())

    called = {"empty": False}

    def fake_empty():
        called["empty"] = True

    monkeypatch.setattr(v, "empty", fake_empty)

    v.clear_items()
    assert called["empty"] is True


def test_visualsprite_large_grid_performance():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 2000, 2000))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.columns = 20

    for _ in range(2000):
        v.add(FakeSprite(w=20, h=20))

    v.arrange_menu_items()

    ys = [v.sprites()[i].rect.y for i in range(0, 2000, 200)]
    assert ys == sorted(ys)


def test_visualsprite_cursor_movement_after_clear():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.columns = 3
    v._2d_movement_dict = {99: ("tb", 1)}

    for _ in range(7):
        v.add(FakeSprite())

    v.arrange_menu_items()

    v.clear_items()
    assert len(v) == 0

    for _ in range(7):
        v.add(FakeSprite())

    v.arrange_menu_items()

    assert v._advance_input(6, 99) == 1


def test_visualsprite_selection_persistence():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.columns = 3

    for _ in range(10):
        v.add(FakeSprite())

    selected = 7

    v.clear_items()
    for _ in range(10):
        v.add(FakeSprite())

    v.arrange_menu_items()

    assert selected < len(v)


def test_total_pages_basic():
    lst = make_list(25)
    lst.page_size = 10

    assert lst.total_pages == 3  # 10 + 10 + 5


def test_total_pages_no_page_size():
    lst = make_list(25)
    lst.page_size = None

    assert lst.total_pages == 1


def test_has_next_prev_page():
    lst = make_list(30)
    lst.page_size = 10

    lst.current_page = 0
    assert lst.has_next_page
    assert not lst.has_prev_page

    lst.current_page = 1
    assert lst.has_next_page
    assert lst.has_prev_page

    lst.current_page = 2
    assert not lst.has_next_page
    assert lst.has_prev_page


def test_set_page_clamps():
    lst = make_list(20)
    lst.page_size = 10

    lst.set_page(0)
    assert lst.current_page == 0

    lst.set_page(1)
    assert lst.current_page == 1

    lst.set_page(5)  # too high → clamp
    assert lst.current_page == 1

    lst.set_page(-3)  # too low → clamp
    assert lst.current_page == 0


def test_page_label():
    lst = make_list(25)
    lst.page_size = 10

    lst.current_page = 0
    assert lst.page_label() == "1/3"

    lst.current_page = 2
    assert lst.page_label() == "3/3"

    lst.page_size = None
    assert lst.page_label() == ""


def test_layout_respects_pagination():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()

    lst = VisualSpriteList(parent=parent)
    lst.rect = Rect(0, 0, 200, 200)
    lst.page_size = 3

    sprites = [FakeSprite() for _ in range(6)]
    for s in sprites:
        lst.add(s)

    lst.columns = 1
    lst.line_spacing = 20

    lst.current_page = 0
    lst.arrange_menu_items()

    assert sprites[0].rect.topleft == (0, 0)
    assert sprites[1].rect.topleft == (0, 20)
    assert sprites[2].rect.topleft == (0, 40)

    assert sprites[3].rect.topleft == (0, 0)
    assert sprites[4].rect.topleft == (0, 0)
    assert sprites[5].rect.topleft == (0, 0)

    lst.current_page = 1
    lst.arrange_menu_items()

    assert sprites[3].rect.topleft == (0, 0)
    assert sprites[4].rect.topleft == (0, 20)
    assert sprites[5].rect.topleft == (0, 40)


def test_cursor_safe_page_switching():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    lst = VisualSpriteList(parent=parent)
    lst.columns = 3
    lst.page_size = 6

    for _ in range(12):
        lst.add(FakeSprite())

    old_index = 2
    old_col = old_index % lst.columns
    assert old_col == 2

    new_local = old_col
    new_global = 6 + new_local

    assert new_global == 8


@pytest.mark.parametrize(
    "start, action, expected",
    [
        pytest.param(0, "next", 1, id="next-from-0"),
        pytest.param(1, "next", 2, id="next-from-1"),
        pytest.param(2, "next", 2, id="next-clamped"),
        pytest.param(2, "next_wrap", 0, id="wrap-next"),
        pytest.param(0, "prev_wrap", 2, id="wrap-prev"),
        pytest.param(1, "prev", 0, id="prev-from-1"),
        pytest.param(0, "prev", 0, id="prev-clamped"),
    ],
)
def test_page_navigation_parametrized(start, action, expected):
    lst = make_list(25)
    lst.page_size = 10
    lst.current_page = start

    if action == "next":
        lst.next_page()
    elif action == "prev":
        lst.prev_page()
    elif action == "next_wrap":
        lst.next_page_wrap()
    elif action == "prev_wrap":
        lst.prev_page_wrap()

    assert lst.current_page == expected


@pytest.mark.parametrize(
    "count, page_size, page, expected",
    [
        pytest.param(7, None, 0, list(range(7)), id="no-page-size"),
        pytest.param(25, 10, 0, list(range(0, 10)), id="page0"),
        pytest.param(25, 10, 1, list(range(10, 20)), id="page1"),
        pytest.param(25, 10, 2, list(range(20, 25)), id="page2"),
        pytest.param(0, 10, 0, [], id="empty"),
    ],
)
def test_visible_indices_parametrized(count, page_size, page, expected):
    lst = make_list(count)
    lst.page_size = page_size
    lst.current_page = page
    assert list(lst._visible_indices()) == expected


@pytest.mark.parametrize(
    "rectangular, orientation, start, button, expected",
    [
        pytest.param(
            False, "horizontal", 1, buttons.RIGHT, 2, id="normal-right"
        ),
        pytest.param(
            False, "horizontal", 2, buttons.DOWN, 5, id="normal-down"
        ),
        pytest.param(
            False,
            "horizontal",
            5,
            buttons.DOWN,
            None,
            id="normal-down-out-of-bounds",
        ),
        pytest.param(True, "horizontal", 1, buttons.DOWN, 4, id="rect-down"),
        pytest.param(True, "horizontal", 5, buttons.UP, 2, id="rect-up"),
        pytest.param(True, "horizontal", 2, buttons.RIGHT, 3, id="rect-right"),
        pytest.param(False, "vertical", 0, buttons.RIGHT, 1, id="vert-right"),
        pytest.param(False, "vertical", 2, buttons.DOWN, 3, id="vert-down"),
        pytest.param(False, "vertical", 2, buttons.UP, 1, id="vert-up"),
    ],
)
def test_advance_input_parametrized(
    rectangular, orientation, start, button, expected
):
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.columns = 3
    v.page_size = 6
    v.rectangular = rectangular
    v.orientation = orientation

    for _ in range(12):
        v.add(FakeSprite())

    v.current_page = 0
    v.arrange_menu_items()

    if expected is None:
        with pytest.raises(IndexError):
            v._advance_input(start, button)
    else:
        assert v._advance_input(start, button) == expected


@pytest.mark.parametrize(
    "orientation, expand",
    [
        pytest.param("horizontal", True, id="h-expand"),
        pytest.param("horizontal", False, id="h-no-expand"),
        pytest.param("vertical", True, id="v-expand"),
        pytest.param("vertical", False, id="v-no-expand"),
    ],
)
def test_visualsprite_spacing_parametrized(orientation, expand):
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.orientation = orientation
    v.expand = expand

    for _ in range(4):
        v.add(FakeSprite(w=20, h=20))

    v.arrange_menu_items()

    ys = [s.rect.y for s in v.sprites()]
    diffs = [b - a for a, b in zip(ys, ys[1:])]

    if expand:
        assert max(diffs) - min(diffs) < 5
    else:
        assert all(abs(d - 24) < 2 for d in diffs)


def test_rectangular_movement_with_pagination():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.rectangular = True
    v.columns = 3
    v.page_size = 6

    # 12 items → 2 pages
    for _ in range(12):
        v.add(FakeSprite())

    # Page 0: indices 0-5
    v.current_page = 0
    v.arrange_menu_items()

    # Virtual rectangle for page 0:
    # 0 1 2
    # 3 4 5
    # 6 7 8 (virtual)
    # DOWN from 3 → 6 → 6 % 6 = 0
    assert v._advance_input(3, buttons.DOWN) == 0

    # Page 1: indices 6-11
    v.current_page = 1
    v.arrange_menu_items()

    # Virtual rectangle for page 1:
    # 6 7 8
    # 9 10 11
    # 12 13 14 (virtual)
    # DOWN from 9 → 12 → 12 % 6 = 0 → global index = 6 + 0 = 6
    assert v._advance_input(9, buttons.DOWN) == 6


def test_vertical_movement_with_pagination():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()

    v = VisualSpriteList(parent=parent)
    v.orientation = "vertical"
    v.columns = 2
    v.page_size = 4

    # 8 items → 2 pages
    for _ in range(8):
        v.add(FakeSprite())

    # Page 0: indices 0-3
    v.current_page = 0
    v.arrange_menu_items()

    # In vertical mode, LR becomes TB
    # So LR(+1) → TB(+1)
    assert v._advance_input(0, buttons.RIGHT) == 1

    # Page 1: indices 4-7
    v.current_page = 1
    v.arrange_menu_items()

    # Same logic, but offset by page
    assert v._advance_input(4, buttons.RIGHT) == 5


@pytest.mark.parametrize(
    "enabled_flags, page_size, current_page, old_index, expected",
    [
        pytest.param(
            [True, True, True],
            3,
            0,
            1,
            1,
            id="single-page-no-change",
        ),
        pytest.param(
            [True, True, True, True],
            3,
            1,
            0,
            3,
            id="page2-first-enabled",
        ),
        pytest.param(
            [True, True, True, False, False, False],
            3,
            1,
            2,
            3,
            id="page2-only-first-enabled",
        ),
        pytest.param(
            [False, False, False, False, False, False],
            3,
            1,
            2,
            3,
            id="page2-no-enabled-fallback-to-first-visible",
        ),
        pytest.param(
            [True, True, True, False, True, False],
            3,
            1,
            0,
            4,
            id="page2-skip-disabled-pick-first-enabled",
        ),
        pytest.param(
            [True, True, True, True, False, True],
            3,
            1,
            5,
            3,
            id="old-index-outside-visible-range",
        ),
        pytest.param(
            [True, False, True, True, False, True],
            2,
            2,
            0,
            4,
            id="multi-page-nonuniform-enabled",
        ),
        pytest.param(
            [True, True, True, True, True, True],
            2,
            2,
            10,
            4,
            id="old-index-huge-out-of-range",
        ),
        pytest.param(
            [True],
            3,
            0,
            0,
            0,
            id="single-item",
        ),
        pytest.param(
            [],
            3,
            0,
            0,
            0,
            id="empty-list-visible-empty",
        ),
    ],
)
def test_snap_selection(
    enabled_flags, page_size, current_page, old_index, expected
):
    lst = make_list_snap(enabled_flags, page_size, current_page)
    result = lst.snap_selection(old_index)
    assert result == expected


def test_visible_enabled_keeps_selection():
    lst = make_list_snap([True, True, True], 3, 0)
    assert lst.snap_selection(1) == 1


def test_visible_mixed_enabled_snaps_to_first_enabled():
    lst = make_list_snap([True, True, True, True, False, True], 3, 1)
    assert lst.snap_selection(5) == 3


def test_visible_all_disabled_falls_back_to_first_visible():
    lst = make_list_snap([False, False, False, False, False, False], 3, 1)
    assert lst.snap_selection(2) == 3


def test_not_visible_page3_snaps_to_first_enabled():
    lst = make_list_snap([True, True, True, False, True, False], 3, 1)
    assert lst.snap_selection(0) == 4


def test_not_visible_page3_no_enabled_falls_back_to_first_visible():
    lst = make_list_snap([True, True, True, False, False, False], 3, 1)
    assert lst.snap_selection(2) == 3


def test_not_visible_page2_snaps_to_first_visible_even_if_disabled():
    lst = make_list_snap([True, False, True, True, False, True], 2, 2)
    assert lst.snap_selection(0) == 4


def test_not_visible_page2_large_old_index_snaps_to_first_visible():
    lst = make_list_snap([True, True, True, True, True, True], 2, 2)
    assert lst.snap_selection(10) == 4


def test_advance_ragged_tb_mid_grid():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 3
    for _ in range(7):
        v.add(FakeSprite())

    visible = list(v._visible_indices())
    assert v._advance_ragged_tb(0, 1, visible) == 3


def test_advance_single_column_wraps():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 1
    for _ in range(5):
        v.add(FakeSprite())

    visible = list(v._visible_indices())
    assert v._advance_single_column(4, 1, visible) == 0  # bottom → top
    assert v._advance_single_column(0, -1, visible) == 4  # top → bottom


def test_arrange_respects_explicit_line_spacing_over_expand():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.expand = True
    v.line_spacing = 30  # explicit → must win
    v.columns = 1
    for _ in range(4):
        v.add(FakeSprite(w=20, h=20))

    v.arrange_menu_items()
    ys = [s.rect.y for s in v.sprites()]
    diffs = [b - a for a, b in zip(ys, ys[1:])]
    assert all(d == 30 for d in diffs), (
        f"expected spacing 30 everywhere, got {diffs}"
    )


def test_arrange_repeated_sprites_call_stable():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 2
    for _ in range(4):
        v.add(FakeSprite(w=20, h=20))

    v.arrange_menu_items()
    pos_a = [s.rect.topleft for s in v.sprites()]
    v.arrange_menu_items()
    pos_b = [s.rect.topleft for s in v.sprites()]
    assert pos_a == pos_b


def test_columns_setter_triggers_needs_arrange():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    for _ in range(4):
        v.add(FakeSprite())

    v.arrange_menu_items()
    assert v._needs_arrange is False

    v.columns = 2
    assert v._needs_arrange is True


def test_columns_setter_changes_layout():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 200, 200))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 1
    for _ in range(4):
        v.add(FakeSprite(w=20, h=20))

    v.arrange_menu_items()
    single_col_ys = [s.rect.y for s in v.sprites()]

    v.columns = 2
    v.arrange_menu_items()
    two_col_ys = [s.rect.y for s in v.sprites()]

    assert single_col_ys != two_col_ys


def test_visible_indices_page_size_larger_than_count():
    lst = make_list(3)
    lst.page_size = 10
    lst.current_page = 0
    assert list(lst._visible_indices()) == [0, 1, 2]


def test_cursor_safe_page_switching_via_snap():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    lst = VisualSpriteList(parent=parent)
    lst.columns = 3
    lst.page_size = 6
    for _ in range(12):
        lst.add(FakeSprite())

    lst.current_page = 0
    lst.arrange_menu_items()

    lst.next_page()
    snapped = lst.snap_selection(2)

    assert snapped in list(lst._visible_indices())


def test_selection_persistence_via_snap():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    lst = VisualSpriteList(parent=parent)
    lst.columns = 3
    lst.page_size = 6
    for _ in range(10):
        lst.add(FakeSprite())

    lst.current_page = 0
    lst.arrange_menu_items()
    selected = 7  # on page 1

    lst.clear_items()
    for _ in range(10):
        lst.add(FakeSprite())
    lst.arrange_menu_items()

    snapped = lst.snap_selection(selected)
    assert snapped in list(lst._visible_indices())


def test_advance_ragged_tb_boundary_raises():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 3
    for _ in range(7):
        v.add(FakeSprite())

    visible = list(v._visible_indices())

    with pytest.raises(IndexError):
        v._advance_ragged_tb(0, -1, visible)

    model = GridIndexModel(
        count=len(visible),
        columns=3,
        rectangular=False,
        orientation="horizontal",
    )
    last_tb = max(model.lr_to_tb(i) for i in range(len(visible)))
    last_lr = model.tb_to_lr(last_tb)
    with pytest.raises(IndexError):
        v._advance_ragged_tb(last_lr, 1, visible)


def test_advance_ragged_lr_wraps_not_raises():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 3
    for _ in range(7):
        v.add(FakeSprite())

    visible = list(v._visible_indices())
    # LR 6 is the lone item in row 2; move_lr wraps: (6+1) % 7 = 0
    result = v._advance_ragged_lr(6, "lr", 1, visible)
    assert result == 0


def test_advance_ragged_lr_valid_move():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 3
    for _ in range(7):
        v.add(FakeSprite())

    visible = list(v._visible_indices())
    assert v._advance_ragged_lr(0, "lr", 1, visible) == 1


def test_advance_rectangular_wraps_at_end():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 3
    v.rectangular = True
    for _ in range(7):
        v.add(FakeSprite())

    visible = list(v._visible_indices())
    result = v._advance_rectangular(6, "tb", 1, visible)
    assert result == 0


def make_list_movement(enabled_flags, columns=3, orientation="horizontal"):
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = columns
    v.orientation = orientation
    for flag in enabled_flags:
        v.add(FakeSprite(enabled=flag))
    v.arrange_menu_items()
    return v


def make_event(button):
    class E:
        pressed = True

    E.button = button
    return E


def test_movement_skips_single_disabled_item():
    v = make_list_movement([True, False, True, True, True, True])
    e = make_event(buttons.RIGHT)
    # From 0, right → 1 (disabled) → skip → 2
    assert v.determine_cursor_movement(0, e) == 2


def test_movement_skips_multiple_consecutive_disabled():
    v = make_list_movement([True, False, False, False, True, True])
    e = make_event(buttons.RIGHT)
    # From 0 → 1,2,3 all disabled → land on 4
    assert v.determine_cursor_movement(0, e) == 4


def test_movement_all_disabled_returns_original():
    v = make_list_movement([False, False, False, False, False, False])
    e = make_event(buttons.RIGHT)
    assert v.determine_cursor_movement(2, e) == 2


def test_movement_no_press_returns_original():
    v = make_list_movement([True, True, True])

    class E:
        pressed = False
        button = buttons.RIGHT

    assert v.determine_cursor_movement(1, E) == 1


def test_movement_empty_list_returns_zero():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)

    class E:
        pressed = True
        button = buttons.RIGHT

    assert v.determine_cursor_movement(0, E) == 0


def test_movement_does_not_land_on_disabled():
    flags = [True, False, True, False, True, True, False, True, True]
    v = make_list_movement(flags, columns=3)

    sprites = v.sprites()
    for start in range(len(v)):
        if not sprites[start].enabled:
            continue
        for button in (buttons.LEFT, buttons.RIGHT, buttons.UP, buttons.DOWN):
            e = make_event(button)
            result = v.determine_cursor_movement(start, e)
            assert sprites[result].enabled, (
                f"cursor landed on disabled item {result} "
                f"(start={start}, button={button})"
            )


def test_movement_with_pagination_stays_on_page():
    parent = RelativeGroup(parent=lambda: Rect(0, 0, 300, 300))
    parent.update_rect_from_parent()
    v = VisualSpriteList(parent=parent)
    v.columns = 3
    v.page_size = 6
    for _ in range(12):
        v.add(FakeSprite())
    v.current_page = 0
    v.arrange_menu_items()

    visible = set(v._visible_indices())
    for button in (buttons.LEFT, buttons.RIGHT, buttons.UP, buttons.DOWN):
        e = make_event(button)
        for start in list(visible):
            result = v.determine_cursor_movement(start, e)
            assert result in visible, (
                f"cursor left page: start={start}, button={button}, result={result}"
            )


def test_movement_vertical_orientation_does_not_land_on_disabled():
    flags = [True, False, True, True, False, True]
    v = make_list_movement(flags, columns=2, orientation="vertical")

    sprites = v.sprites()
    for start in range(len(v)):
        if not sprites[start].enabled:
            continue
        for button in (buttons.LEFT, buttons.RIGHT, buttons.UP, buttons.DOWN):
            e = make_event(button)
            result = v.determine_cursor_movement(start, e)
            assert sprites[result].enabled, (
                f"vertical: cursor landed on disabled {result} "
                f"(start={start}, button={button})"
            )


def test_movement_boundary_up_from_tb_zero():
    """
    The only hard boundary in ragged TB movement is moving UP
    from the item at TB index 0. Every other move wraps across columns.

    Grid (3 cols, 7 items):
        0  1  2
        3  4  5
        6  _  _
    TB order: 0,3,6,1,4,2,5
    TB index 0 = LR index 0. Moving UP → new_tb = -1 → IndexError.
    """
    v = make_list_movement([True] * 7, columns=3)
    e = make_event(buttons.UP)
    # LR 0 is at TB 0 → moving up raises → cursor stays at 0
    assert v.determine_cursor_movement(0, e) == 0


def test_movement_tb_wraps_across_columns():
    """
    TB movement wraps across columns — DOWN from the last item in a
    column continues at the top of the next column, not a boundary.

    Grid (3 cols, 7 items):
        0  1  2
        3  4  5
        6  _  _
    DOWN from 6 (col 0 row 2, TB 2) → TB 3 → LR 1.
    """
    v = make_list_movement([True] * 7, columns=3)
    e = make_event(buttons.DOWN)
    assert v.determine_cursor_movement(6, e) == 1


@pytest.mark.parametrize(
    "flags, start, button, expected",
    [
        pytest.param(
            [True, True, True, True, True, True],
            0,
            buttons.RIGHT,
            1,
            id="simple-right",
        ),
        pytest.param(
            [True, True, True, True, True, True],
            2,
            buttons.DOWN,
            5,
            id="simple-down",
        ),
        pytest.param(
            [True, False, True, True, True, True],
            0,
            buttons.RIGHT,
            2,
            id="skip-one-disabled",
        ),
        pytest.param(
            [True, True, True, True, True, True],
            0,
            buttons.UP,
            0,
            id="boundary-up-tb-zero-stays",
        ),
        pytest.param(
            [True] * 7,
            6,
            buttons.DOWN,
            1,
            id="down-from-last-ragged-wraps-to-col1",
        ),
    ],
)
def test_determine_cursor_movement_parametrized(
    flags, start, button, expected
):
    v = make_list_movement(flags, columns=3)
    e = make_event(button)
    assert v.determine_cursor_movement(start, e) == expected
