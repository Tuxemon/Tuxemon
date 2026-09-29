# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.camera.camera import Camera, CameraController
from tuxemon.platform.const import intentions


@pytest.fixture
def handler():
    camera = MagicMock(spec=Camera)
    return CameraController(camera)


@pytest.fixture
def camera(handler):
    return handler.camera


def test_handle_input_free_roaming_held_up(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = True
    event.pressed = False
    event.button = intentions.UP
    handler.handle_input(event)
    camera.move.assert_called_once_with(dx=0, dy=-handler.speed)


def test_handle_input_free_roaming_pressed_down(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = False
    event.pressed = True
    event.button = intentions.DOWN
    handler.handle_input(event)
    camera.move.assert_called_once_with(dx=0, dy=handler.speed)


def test_handle_input_free_roaming_disabled(handler, camera):
    camera.free_roaming_enabled = False
    event = MagicMock()
    event.held = True
    event.button = intentions.UP
    handler.handle_input(event)
    camera.move.assert_not_called()


def test_handle_input_return_event(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = True
    event.button = intentions.UP
    returned_event = handler.handle_input(event)
    assert returned_event == event


def test_handle_input_left(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = True
    event.button = intentions.LEFT
    handler.handle_input(event)
    camera.move.assert_called_once_with(dx=-handler.speed, dy=0)


def test_handle_input_right(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = True
    event.button = intentions.RIGHT
    handler.handle_input(event)
    camera.move.assert_called_once_with(dx=handler.speed, dy=0)


def test_handle_input_no_action(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = False
    event.pressed = False
    event.button = intentions.UP
    result = handler.handle_input(event)
    assert result is None
    camera.move.assert_not_called()


def test_handle_input_invalid_direction(handler, camera):
    camera.free_roaming_enabled = True
    event = MagicMock()
    event.held = True
    event.button = 999
    result = handler.handle_input(event)
    assert result == event
    camera.move.assert_not_called()
