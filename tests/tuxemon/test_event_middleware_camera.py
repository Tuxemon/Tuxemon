# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventmiddleware import CameraControlMiddleware
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput


@pytest.fixture
def mock_camera_manager():
    return MagicMock()


@pytest.fixture
def mw(mock_camera_manager):
    return CameraControlMiddleware(mock_camera_manager)


def test_camera_moves_when_detached(mw, mock_camera_manager):
    camera = MagicMock()
    camera.is_following.return_value = False
    mock_camera_manager.get_active_camera.return_value = camera

    event = PlayerInput(button=intentions.UP, value=1, hold_time=0)

    result = mw.preprocess(event)

    assert result == mock_camera_manager.handle_input.return_value
    mock_camera_manager.handle_input.assert_called_once_with(event)


def test_camera_passes_event_when_following(mw, mock_camera_manager):
    camera = MagicMock()
    camera.is_following.return_value = True
    mock_camera_manager.get_active_camera.return_value = camera

    event = PlayerInput(button=intentions.UP, value=1, hold_time=0)

    result = mw.preprocess(event)

    assert result is event
    mock_camera_manager.handle_input.assert_not_called()


def test_non_directional_passes_through(mw):
    event = PlayerInput(button=9999, value=1, hold_time=0)
    assert mw.preprocess(event) is event
