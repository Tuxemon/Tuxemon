# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pygame as pg
import pytest
from pygame.event import Event

from tuxemon.platform.const import buttons
from tuxemon.platform.platform_pygame.events import (
    HORIZONTAL_AXIS,
    VERTICAL_AXIS,
    InputMappingStrategy,
    PygameGamepadInput,
)


class MockMapping(InputMappingStrategy):
    def __init__(self, event_map: dict[int, str]):
        self.event_map = event_map

    def map_button(self, raw_button_id: int):
        return self.event_map.get(raw_button_id)

    def map_axis(self, axis_id: int, value: float):
        if axis_id == HORIZONTAL_AXIS:
            button = buttons.RIGHT if value > 0 else buttons.LEFT
        elif axis_id == VERTICAL_AXIS:
            button = buttons.DOWN if value > 0 else buttons.UP
        else:
            return (None, False)

        pressed = abs(value) > 0.2
        return (button, pressed)


@pytest.fixture(scope="module")
def gamepad_input():
    pg.quit()
    pg.init()
    mock_js = Mock()
    mock_js.get_instance_id.return_value = 0
    event_map = {
        0: buttons.A,
        1: buttons.B,
        6: buttons.BACK,
        11: buttons.LEFT,
        12: buttons.RIGHT,
        13: buttons.UP,
        14: buttons.DOWN,
        7: buttons.START,
    }
    strategy = MockMapping(event_map)
    gp = PygameGamepadInput(strategy, [mock_js])
    gp.press = Mock()
    gp.release = Mock()
    yield gp
    pg.quit()


@pytest.fixture(autouse=True)
def reset_mocks(gamepad_input):
    gamepad_input.press.reset_mock()
    gamepad_input.release.reset_mock()


def test_handle_button_press(gamepad_input):
    gamepad_input.handle_button(buttons.A, True)
    gamepad_input.press.assert_called_once_with(buttons.A, 0.0)


def test_handle_button_release(gamepad_input):
    gamepad_input.handle_button(buttons.A, False)
    gamepad_input.release.assert_called_once_with(buttons.A)


def test_check_button_press(gamepad_input):
    event = Event(pg.JOYBUTTONDOWN, button=0, joy=0)
    gamepad_input.process_event(event)
    gamepad_input.press.assert_called_once_with(buttons.A, 0.0)


def test_check_button_release(gamepad_input):
    event = Event(pg.JOYBUTTONUP, button=0, joy=0)
    gamepad_input.process_event(event)
    gamepad_input.release.assert_called_once_with(buttons.A)


@pytest.mark.parametrize(
    "axis, value, expected",
    [
        pytest.param(
            HORIZONTAL_AXIS, 0.5, buttons.RIGHT, id="horizontal_right"
        ),
        pytest.param(
            HORIZONTAL_AXIS, -0.5, buttons.LEFT, id="horizontal_left"
        ),
        pytest.param(VERTICAL_AXIS, 0.5, buttons.DOWN, id="vertical_down"),
        pytest.param(VERTICAL_AXIS, -0.5, buttons.UP, id="vertical_up"),
    ],
)
def test_axis_motion(gamepad_input, axis, value, expected):
    event = Event(pg.JOYAXISMOTION, axis=axis, value=value, joy=0)
    gamepad_input.process_event(event)
    gamepad_input.press.assert_called_with(expected, abs(value))


@pytest.mark.parametrize(
    "axis, prev_state, value, expected_release",
    [
        pytest.param(
            HORIZONTAL_AXIS,
            -1,
            0.1,
            buttons.LEFT,
            id="release_left_small_change",
        ),
        pytest.param(
            VERTICAL_AXIS, -1, 0.1, buttons.UP, id="release_up_small_change"
        ),
        pytest.param(HORIZONTAL_AXIS, 1, 0.6, None, id="no_release_no_press"),
    ],
)
def test_axis_small_or_no_change(
    gamepad_input, axis, prev_state, value, expected_release
):
    gamepad_input.axis_state[axis] = prev_state
    event = Event(pg.JOYAXISMOTION, axis=axis, value=value, joy=0)
    gamepad_input.process_event(event)

    if expected_release:
        gamepad_input.release.assert_any_call(expected_release)
    else:
        gamepad_input.press.assert_not_called()
        gamepad_input.release.assert_not_called()


def test_ignores_unhandled_event_type(gamepad_input):
    event = Event(pg.JOYDEVICEADDED, device_index=0)
    gamepad_input.process_event(event)
    gamepad_input.press.assert_not_called()
    gamepad_input.release.assert_not_called()


def test_hat_motion_left_right(gamepad_input):
    gamepad_input.hat_state = (0, 0)

    event = Event(pg.JOYHATMOTION, value=(-1, 0), joy=0)
    gamepad_input.process_event(event)
    gamepad_input.press.assert_any_call(buttons.LEFT, 0.0)

    gamepad_input.press.reset_mock()
    gamepad_input.release.reset_mock()

    event = Event(pg.JOYHATMOTION, value=(1, 0), joy=0)
    gamepad_input.process_event(event)
    gamepad_input.release.assert_any_call(buttons.LEFT)
    gamepad_input.press.assert_any_call(buttons.RIGHT, 0.0)


def test_hat_motion_up_down(gamepad_input):
    event = Event(pg.JOYHATMOTION, value=(0, -1), joy=0)
    gamepad_input.process_event(event)
    gamepad_input.press.assert_any_call(buttons.UP, 0.0)

    event = Event(pg.JOYHATMOTION, value=(0, 1), joy=0)
    gamepad_input.process_event(event)
    gamepad_input.press.assert_any_call(buttons.DOWN, 0.0)


def test_hat_release(gamepad_input):
    gamepad_input.hat_state = (-1, 0)
    event = Event(pg.JOYHATMOTION, value=(0, 0), joy=0)
    gamepad_input.process_event(event)
    gamepad_input.release.assert_any_call(buttons.LEFT)


def test_axis_direction_change(gamepad_input):
    gamepad_input.axis_state[HORIZONTAL_AXIS] = 1
    event = Event(pg.JOYAXISMOTION, axis=HORIZONTAL_AXIS, value=-0.6, joy=0)
    gamepad_input.process_event(event)
    gamepad_input.release.assert_any_call(buttons.RIGHT)
    gamepad_input.press.assert_any_call(buttons.LEFT, 0.6)


@pytest.mark.parametrize(
    "event",
    [
        pytest.param(
            Event(pg.JOYBUTTONDOWN, button=99, joy=0), id="unknown_button"
        ),
        pytest.param(
            Event(pg.JOYAXISMOTION, axis=99, value=0.5, joy=0),
            id="unknown_axis",
        ),
    ],
)
def test_unknown_inputs_are_ignored(gamepad_input, event):
    gamepad_input.process_event(event)
    gamepad_input.press.assert_not_called()
    gamepad_input.release.assert_not_called()
