# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.menu.cursor import (
    CURSOR_X_RATIO_DENOMINATOR,
    CURSOR_Y_RATIO_DENOMINATOR,
    MenuCursorController,
)
from tuxemon.sprite import SpriteGroup


@pytest.fixture
def menu_sprites():
    return SpriteGroup()


@pytest.fixture
def fake_context():
    ctx = MagicMock()
    ctx.scaling = MagicMock()
    ctx.scaling.scale_int = lambda x: x * 2
    ctx.scaling.scale_tuple = lambda t: tuple(x * 2 for x in t)
    return ctx


@pytest.fixture
def controller(menu_sprites, fake_context):
    cursor_filename = "gfx/arrow.png"
    get_selected_item = MagicMock(return_value=None)
    animate = MagicMock(return_value=None)
    duration = 1.0
    remove_animations = MagicMock()
    ctrl = MenuCursorController(
        cursor_filename,
        menu_sprites,
        get_selected_item,
        animate,
        duration,
        fake_context,
        remove_animations,
    )
    return ctrl


def test_init(controller, menu_sprites):
    assert controller.arrow is not None
    assert controller.sprites is menu_sprites
    assert controller.get_item is controller.get_item
    assert controller.animate is controller.animate
    assert controller.duration == 1.0
    assert controller.remove_animations is controller.remove_animations


def test_get_margin(controller):
    margin = controller.get_margin()
    assert isinstance(margin, tuple)
    assert len(margin) == 2


def test_show_cursor(controller):
    controller.hide_cursor()
    controller.show_cursor()
    assert controller.arrow in controller.sprites


def test_hide_cursor(controller):
    controller.show_cursor()
    controller.hide_cursor()
    assert controller.arrow not in controller.sprites


@pytest.mark.parametrize(
    "animate_flag",
    [
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
    ],
)
def test_trigger_cursor_update(controller, animate_flag):
    item = MagicMock()
    item.rect.midleft = (10, 20)
    controller.get_item.return_value = item
    animation = controller.trigger_cursor_update(animate=animate_flag)
    assert animation is None

    if animate_flag:
        controller.animate.assert_called_once()
        controller.remove_animations.assert_called_once_with(
            controller.arrow.rect
        )
    else:
        controller.animate.assert_not_called()


def test_trigger_cursor_update_no_item(controller):
    controller.get_item.return_value = None
    animation = controller.trigger_cursor_update(animate=True)
    assert animation is None


def test_update_selection_focus(controller):
    previous_item = MagicMock()
    new_item = MagicMock()
    controller.update_selection_focus(previous_item, new_item)
    assert previous_item.in_focus is False
    assert new_item.in_focus is True
    previous_item.update_image.assert_called_once()
    new_item.update_image.assert_called_once()


def test_update_selection_focus_no_previous_item(controller):
    new_item = MagicMock()
    controller.update_selection_focus(None, new_item)
    assert new_item.in_focus is True
    new_item.update_image.assert_called_once()


def test_update_selection_focus_no_new_item(controller):
    previous_item = MagicMock()
    controller.update_selection_focus(previous_item, None)
    assert previous_item.in_focus is False
    previous_item.update_image.assert_called_once()


def test_update_focus(controller):
    item = MagicMock()
    controller._update_focus(item, True)
    assert item.in_focus is True
    item.update_image.assert_called_once()


def test_ensure_cursor_visible(controller):
    controller._ensure_cursor_visible(True)
    assert controller.arrow in controller.sprites
    controller._ensure_cursor_visible(False)
    assert controller.arrow not in controller.sprites


def test_ensure_cursor_visible_already_visible(controller):
    controller.show_cursor()
    controller._ensure_cursor_visible(True)
    assert controller.arrow in controller.sprites


def test_ensure_cursor_visible_already_hidden(controller):
    controller.hide_cursor()
    controller._ensure_cursor_visible(False)
    assert controller.arrow not in controller.sprites


def test_cursor_position_consistency(controller):
    item = MagicMock()
    item.rect.midleft = (10, 20)
    controller.get_item.return_value = item

    # Non-animated path
    controller.trigger_cursor_update(animate=False)
    static_pos = controller.arrow.rect.midright

    # Animated path
    controller.animate.reset_mock()
    controller.remove_animations.reset_mock()

    controller.trigger_cursor_update(animate=True)

    # Simulate animation system applying final values
    controller.arrow.rect.right = 10
    controller.arrow.rect.centery = 20
    animated_pos = controller.arrow.rect.midright

    assert static_pos == animated_pos


def test_trigger_cursor_update_with_offsets(menu_sprites, fake_context):
    # Create controller with offsets
    ctrl = MenuCursorController(
        "gfx/arrow.png",
        menu_sprites,
        get_selected_item=MagicMock(),
        animate=MagicMock(),
        duration=1.0,
        context=fake_context,
        remove_animations=MagicMock(),
        offset=(5, -3),
    )

    item = MagicMock()
    item.rect.midleft = (10, 20)
    ctrl.get_item.return_value = item

    ctrl.trigger_cursor_update(animate=False)

    # midright should include offsets
    assert ctrl.arrow.rect.midright == (10 + 5, 20 - 3)


def test_update_focus_idempotent(controller):
    item = MagicMock()
    item.in_focus = True

    controller._update_focus(item, True)

    # update_image should NOT be called because nothing changed
    item.update_image.assert_not_called()


def test_show_cursor_idempotent(controller):
    controller.show_cursor()
    controller.show_cursor()
    controller.show_cursor()

    # SpriteGroup should contain cursor exactly once
    assert list(controller.sprites).count(controller.arrow) == 1


def test_hide_cursor_idempotent(controller):
    controller.show_cursor()
    controller.hide_cursor()
    controller.hide_cursor()
    controller.hide_cursor()

    assert controller.arrow not in controller.sprites


def test_cursor_moves_when_item_changes(controller):
    item1 = MagicMock()
    item1.rect.midleft = (10, 20)

    item2 = MagicMock()
    item2.rect.midleft = (50, 80)

    controller.get_item.return_value = item1
    controller.trigger_cursor_update(animate=False)
    pos1 = controller.arrow.rect.midright

    controller.get_item.return_value = item2
    controller.trigger_cursor_update(animate=False)
    pos2 = controller.arrow.rect.midright

    assert pos1 != pos2


def test_get_margin_correctness(controller, fake_context):
    mock_img = MagicMock()
    mock_img.get_width.return_value = 100
    mock_img.get_height.return_value = 50

    # Override both so .image property returns the mock
    controller.arrow._image = mock_img
    controller.arrow._original_image = mock_img

    # Prevent update_image() from running
    controller.arrow._needs_update = False

    x, y = controller.get_margin()

    expected_x = -fake_context.scaling.scale_int(
        int(100 / CURSOR_X_RATIO_DENOMINATOR)
    )
    expected_y = -fake_context.scaling.scale_int(
        int(50 / CURSOR_Y_RATIO_DENOMINATOR)
    )

    assert x == expected_x
    assert y == expected_y
