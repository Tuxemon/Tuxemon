# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest
from pygame.rect import Rect

from tuxemon.ui.dialogue import calc_dialog_rect, resolve_reference_rect
from tuxemon.ui.text_alignment import DialogPosition


@pytest.fixture
def screen_rect():
    return Rect(0, 0, 800, 600)


def test_resolve_reference_rect_screen(screen_rect):
    reference_rect = resolve_reference_rect(screen_rect, None)
    assert reference_rect == screen_rect


def test_resolve_reference_rect_rect(screen_rect):
    target = Rect(100, 100, 200, 200)
    reference_rect = resolve_reference_rect(screen_rect, target)
    assert reference_rect == target


def test_resolve_reference_rect_coords(screen_rect):
    target = (100, 100)
    reference_rect = resolve_reference_rect(screen_rect, target)
    assert reference_rect == Rect(100, 100, 1, 1)


def test_calc_dialog_rect_top(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.TOP)
    assert rect.top == screen_rect.top
    assert rect.centerx == screen_rect.centerx


def test_calc_dialog_rect_bottom(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.BOTTOM)
    assert rect.bottom == screen_rect.bottom
    assert rect.centerx == screen_rect.centerx


def test_calc_dialog_rect_center(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.CENTER)
    assert rect.center == screen_rect.center


def test_calc_dialog_rect_topleft(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.TOPLEFT)
    assert rect.topleft == screen_rect.topleft


def test_calc_dialog_rect_topright(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.TOPRIGHT)
    assert rect.topright == screen_rect.topright


def test_calc_dialog_rect_bottomleft(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.BOTTOMLEFT)
    assert rect.bottomleft == screen_rect.bottomleft


def test_calc_dialog_rect_bottomright(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.BOTTOMRIGHT)
    assert rect.bottomright == screen_rect.bottomright


def test_calc_dialog_rect_left(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.LEFT)
    assert rect.left == screen_rect.left
    assert rect.centery == screen_rect.centery


def test_calc_dialog_rect_right(screen_rect):
    rect = calc_dialog_rect(screen_rect, DialogPosition.RIGHT)
    assert rect.right == screen_rect.right
    assert rect.centery == screen_rect.centery


def test_calc_dialog_rect_at_target(screen_rect):
    target = (100, 100)
    rect = calc_dialog_rect(screen_rect, DialogPosition.AT_TARGET, target)
    assert rect.topleft == target


def test_calc_dialog_rect_at_target_invalid(screen_rect):
    target = Rect(100, 100, 200, 200)
    with pytest.raises(ValueError):
        calc_dialog_rect(screen_rect, DialogPosition.AT_TARGET, target)


def test_calc_dialog_rect_invalid_position(screen_rect):
    with pytest.raises(ValueError):
        calc_dialog_rect(screen_rect, "invalid_position")
