# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.menu.input_handler import MenuInputHandler
from tuxemon.platform.const import buttons, intentions
from tuxemon.platform.events import PlayerInput


def make_event(button, pressed=True, value=None):
    event = Mock()
    event.button = button
    event.pressed = pressed
    event.value = value
    return event


def real_event(
    button, value=1, hold_time=1, hold_duration=0.0, previous_value=0
):
    e = PlayerInput(button, value=value)
    e.hold_time = hold_time
    e.hold_duration = hold_duration
    e.previous_value = previous_value
    return e


def fake_menu_items(items):
    menu_items = Mock()

    menu_items_list = items

    menu_items.__iter__ = lambda self=menu_items: iter(menu_items_list)
    menu_items.__getitem__ = lambda self, i: menu_items_list[i]
    menu_items.__len__ = lambda self: len(menu_items_list)

    menu_items.rect = Mock()
    menu_items.rect.left = 0
    menu_items.rect.top = 0
    menu_items.rect.collidepoint.return_value = False

    menu_items.update_rect_from_parent = Mock()

    return menu_items


@pytest.fixture
def menu():
    menu = Mock()
    menu.state_controller.is_enabled.return_value = True
    menu.escape_key_exits = True
    menu.touch_aware = True

    item1 = Mock(enabled=True)
    item1.rect.collidepoint.return_value = False

    item2 = Mock(enabled=True)
    item2.rect.collidepoint.return_value = False

    menu.menu_items = fake_menu_items([item1, item2])
    menu.selected_index = 0
    menu.get_selected_item.return_value = item1

    return menu


@pytest.fixture
def handler(menu):
    return MenuInputHandler(menu)


@pytest.mark.parametrize(
    "button",
    [
        pytest.param(buttons.B, id="button_b"),
        pytest.param(buttons.BACK, id="button_back"),
        pytest.param(intentions.MENU_CANCEL, id="intention_cancel"),
    ],
)
def test_escape_buttons_always_consume(handler, menu, button):
    event = make_event(button)
    assert handler.handle_event(event) is None


@pytest.mark.parametrize(
    "button",
    [
        pytest.param(buttons.A, id="button_a"),
        pytest.param(intentions.SELECT, id="intention_select"),
    ],
)
def test_confirm_buttons_always_consume(handler, menu, button):
    event = make_event(button)
    assert handler.handle_event(event) is None


@pytest.mark.parametrize(
    "button",
    [
        pytest.param(buttons.UP, id="button_up"),
        pytest.param(buttons.DOWN, id="button_down"),
        pytest.param(buttons.LEFT, id="button_left"),
        pytest.param(buttons.RIGHT, id="button_right"),
    ],
)
def test_cursor_buttons_always_consume(handler, menu, button):
    event = make_event(button)
    assert handler.handle_event(event) is None


def test_unhandled_button_propagates(handler, menu):
    FAKE_BUTTON = object()
    event = make_event(FAKE_BUTTON)
    assert handler.handle_event(event) is event


def test_no_enabled_items_prevents_confirm(handler, menu):
    for item in menu.menu_items:
        item.enabled = False

    event = real_event(buttons.A, value=1, hold_time=1)
    handler.handle_event(event)

    menu.on_menu_selection.assert_not_called()


def test_empty_menu_prevents_interaction(handler, menu):
    menu.menu_items = fake_menu_items([])

    event = real_event(buttons.A, value=1, hold_time=1)
    handler.handle_event(event)

    menu.on_menu_selection.assert_not_called()


def test_disabled_menu_prevents_interaction(handler, menu):
    menu.state_controller.is_enabled.return_value = False

    event = real_event(buttons.A, value=1, hold_time=1)
    handler.handle_event(event)

    menu.on_menu_selection.assert_not_called()


def test_mouse_propagates_when_touch_aware_off(handler, menu):
    menu.touch_aware = False
    event = make_event(buttons.MOUSELEFT, value=(10, 10))
    assert handler.handle_event(event) is event


def test_mouse_click_outside_rect_propagates(handler, menu):
    menu.menu_items.rect.collidepoint.return_value = False
    event = make_event(buttons.MOUSELEFT, value=(999, 999))
    assert handler.handle_event(event) is event


def test_mouse_click_on_enabled_item_selects(handler, menu):
    menu.menu_items.rect.collidepoint.return_value = True
    menu.menu_items[1].rect.collidepoint.return_value = True

    event = make_event(buttons.MOUSELEFT, value=(5, 5))
    result = handler.handle_event(event)

    assert result is None
    menu.change_selection.assert_called_once_with(1)
    menu.on_menu_selection.assert_called_once()


def test_mouse_click_hits_no_item_propagates(handler, menu):
    menu.menu_items.rect.collidepoint.return_value = True
    for item in menu.menu_items:
        item.rect.collidepoint.return_value = False

    event = make_event(buttons.MOUSELEFT, value=(5, 5))
    assert handler.handle_event(event) is event


def test_mouse_invalid_position_raises(handler, menu):
    event = make_event(buttons.MOUSELEFT, value="invalid")
    with pytest.raises(ValueError):
        handler.handle_event(event)


def test_valid_press_on_pressed(handler, menu):
    event = real_event(buttons.A, value=1, hold_time=1)
    assert handler._valid_press(event) is True


def test_valid_press_on_held_after_delay(handler, menu):
    event = real_event(
        buttons.A,
        value=1,
        hold_time=10,
        hold_duration=handler.REPEAT_DELAY + 0.1,
    )
    assert handler._valid_press(event) is True


def test_valid_press_on_held_before_delay(handler, menu):
    event = real_event(
        buttons.A,
        value=1,
        hold_time=10,
        hold_duration=handler.REPEAT_DELAY - 0.1,
    )
    assert handler._valid_press(event) is False


def test_fake_press_is_valid_press(handler, menu):
    event = real_event(buttons.RIGHT, value=1, hold_time=10, hold_duration=1.0)

    fake = handler._fake_press(event)

    assert fake.value == 1
    assert fake.previous_value == 0
    assert fake.hold_time == 1
    assert fake.hold_duration == 0.0
    assert fake.pressed is True
    assert fake.held is True


def test_repeat_timer_resets_on_release(handler, menu):
    handler._repeat_timers[buttons.RIGHT] = 123.456

    event = real_event(buttons.RIGHT, value=0, previous_value=1)
    assert event.released is True

    handler.handle_event(event)

    assert handler._repeat_timers[buttons.RIGHT] == 0.0
