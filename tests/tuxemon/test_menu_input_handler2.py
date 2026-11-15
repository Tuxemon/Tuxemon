# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.menu.input_handler import PygameMenuInputHandler
from tuxemon.platform.const import buttons, intentions


@pytest.fixture
def state():
    state = Mock()

    state.state_controller.is_interactive.return_value = True

    state.menu.is_enabled.return_value = True
    state.menu.update = Mock()
    state.menu.get_selected_widget.return_value = "widget"

    state.escape_key_exits = True

    state.open = True

    state.selected_widget = None

    return state


@pytest.fixture
def handler(state):
    return PygameMenuInputHandler(state)


def make_event(button, pressed=True):
    event = Mock()
    event.button = button
    event.pressed = pressed
    return event


def test_non_interactive_propagates(handler, state):
    state.state_controller.is_interactive.return_value = False
    event = make_event(buttons.A)
    assert handler.handle_event(event) is event


def test_disabled_menu_propagates(handler, state):
    state.menu.is_enabled.return_value = False
    event = make_event(buttons.A)
    assert handler.handle_event(event) is event


@pytest.mark.parametrize(
    "button",
    [
        pytest.param(buttons.B, id="button_b"),
        pytest.param(buttons.BACK, id="button_back"),
        pytest.param(intentions.MENU_CANCEL, id="intention_cancel"),
    ],
)
def test_escape_consumes_when_escape_key_exits_false(handler, state, button):
    state.escape_key_exits = False
    event = make_event(button)
    assert handler.handle_event(event) is None


@pytest.mark.parametrize(
    "button",
    [
        pytest.param(buttons.B, id="button_b"),
        pytest.param(buttons.BACK, id="button_back"),
        pytest.param(intentions.MENU_CANCEL, id="intention_cancel"),
    ],
)
def test_escape_propagates_when_escape_key_exits_true(handler, state, button):
    state.escape_key_exits = True
    event = make_event(button)
    handler._convert_event = Mock(return_value=None)
    assert handler.handle_event(event) is event


def test_conversion_failure_propagates(handler, state):
    handler._convert_event = Mock(return_value=None)
    event = make_event(buttons.A)
    assert handler.handle_event(event) is event


def test_conversion_exception_propagates(handler, state):
    handler._convert_event = Mock(side_effect=Exception("boom"))
    event = make_event(buttons.A)
    assert handler.handle_event(event) is event


def test_confirm_button_updates_menu_when_open_and_pressed(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)

    event = make_event(buttons.A, pressed=True)
    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_called_once_with([pygame_event])
    assert state.selected_widget == "widget"


def test_menu_does_not_update_when_not_pressed(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)

    event = make_event(buttons.A, pressed=False)
    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_not_called()


def test_menu_does_not_update_when_closed(handler, state):
    state.open = False
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)

    event = make_event(buttons.A, pressed=True)
    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_not_called()


def test_menu_update_exception_is_logged_and_consumed(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)

    state.menu.update.side_effect = Exception("update failed")

    event = make_event(buttons.A, pressed=True)
    result = handler.handle_event(event)

    assert result is None
    assert state.selected_widget is None


def test_directional_updates_when_is_press_true(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)
    handler._is_press = Mock(return_value=True)

    event = make_event(buttons.UP, pressed=False)
    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_called_once_with([pygame_event])
    handler._is_press.assert_called_once()


def test_directional_does_not_update_when_is_press_false(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)
    handler._is_press = Mock(return_value=False)

    event = make_event(buttons.UP, pressed=False)
    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_not_called()


def test_directional_held_before_delay_no_update(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)

    event = make_event(buttons.UP, pressed=False)
    event.held = True
    event.hold_duration = handler.REPEAT_DELAY - 0.1

    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_not_called()


def test_directional_held_after_delay_updates(handler, state):
    pygame_event = Mock()
    handler._convert_event = Mock(return_value=pygame_event)

    event = make_event(buttons.UP, pressed=False)
    event.held = True
    event.hold_duration = handler.REPEAT_DELAY + 0.1

    result = handler.handle_event(event)

    assert result is None
    state.menu.update.assert_called_once_with([pygame_event])
