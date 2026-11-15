# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventmiddleware import MovementMiddleware
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput


@pytest.fixture
def mock_character():
    c = MagicMock()
    c.slug = "npc_1"
    c.mover = MagicMock()
    return c


@pytest.fixture
def mock_movement_manager():
    return MagicMock()


@pytest.fixture
def mock_camera_manager():
    return MagicMock()


@pytest.fixture
def mw(mock_character, mock_movement_manager, mock_camera_manager):
    return MovementMiddleware(
        mock_character,
        mock_movement_manager,
        mock_camera_manager,
    )


def test_run_updates_movement_state(mw, mock_character):
    event = PlayerInput(
        button=intentions.RUN,
        value=1,
        previous_value=1,
        hold_time=0.2,
    )
    result = mw.preprocess(event)
    mock_character.mover.update_movement_state.assert_called_once_with(True)
    assert result is event


def test_direction_passed_to_camera_if_not_following(mw, mock_camera_manager):
    camera = MagicMock()
    camera.is_following.return_value = False
    mock_camera_manager.get_active_camera.return_value = camera
    event = PlayerInput(
        button=intentions.UP,
        value=1,
        previous_value=1,
        hold_time=0.1,
    )
    result = mw.preprocess(event)
    mw.movement_manager.queue_movement.assert_not_called()
    assert result is event


def test_direction_moves_when_allowed(
    mw, mock_movement_manager, mock_camera_manager
):
    camera = MagicMock()
    camera.is_following.return_value = True
    mock_camera_manager.get_active_camera.return_value = camera
    mock_movement_manager.is_movement_allowed.return_value = True
    event = PlayerInput(
        button=intentions.UP,
        value=1,
        previous_value=1,
        hold_time=0.1,
    )
    result = mw.preprocess(event)
    assert result is None
    mock_movement_manager.queue_movement.assert_called_once()
    mock_movement_manager.move_char.assert_called_once()


def test_direction_queues_but_does_not_move_if_not_allowed(
    mw, mock_movement_manager, mock_camera_manager
):
    camera = MagicMock()
    camera.is_following.return_value = True
    mock_camera_manager.get_active_camera.return_value = camera
    mock_movement_manager.is_movement_allowed.return_value = False
    event = PlayerInput(
        button=intentions.UP,
        value=1,
        previous_value=1,
        hold_time=0.1,
    )
    result = mw.preprocess(event)
    assert result is None
    mock_movement_manager.queue_movement.assert_called_once()
    mock_movement_manager.move_char.assert_not_called()


def test_release_stops_character(
    mw, mock_movement_manager, mock_camera_manager
):
    camera = MagicMock()
    camera.is_following.return_value = True
    mock_camera_manager.get_active_camera.return_value = camera
    mock_movement_manager.has_pending_movement.return_value = True
    event = PlayerInput(
        button=intentions.UP,
        value=0,
        previous_value=1,
        hold_time=0,
    )
    result = mw.preprocess(event)
    assert result is None
    mock_movement_manager.stop_char.assert_called_once()
