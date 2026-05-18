# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pygame
import pytest
from pygame.rect import Rect
from pygame.surface import Surface

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
