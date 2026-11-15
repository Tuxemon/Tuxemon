# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import Direction
from tuxemon.entity.npc import NPC
from tuxemon.event.eventmanager import EventManager
from tuxemon.movement import MovementManager
from tuxemon.platform.input_manager import InputManager


@pytest.fixture
def mock_event_manager():
    return MagicMock(spec=EventManager)


@pytest.fixture
def mock_input_manager():
    return MagicMock(spec=InputManager)


@pytest.fixture
def movement_manager(mock_event_manager, mock_input_manager):
    return MovementManager(
        mock_event_manager,
        mock_input_manager,
    )


@pytest.fixture
def mock_npc():
    npc = MagicMock(spec=NPC)
    npc.slug = "npc_1"
    return npc


def test_queue_movement(movement_manager):
    movement_manager.queue_movement("npc_1", Direction.UP)
    assert movement_manager.wants_to_move_char["npc_1"] == Direction.UP


def test_move_char_calls_set_move_direction(movement_manager, mock_npc):
    movement_manager.move_char(mock_npc, Direction.LEFT)
    mock_npc.set_move_direction.assert_called_once_with(Direction.LEFT)


def test_stop_char(movement_manager, mock_npc, mock_event_manager):
    movement_manager.wants_to_move_char["npc_1"] = Direction.UP
    movement_manager.stop_char(mock_npc)
    assert "npc_1" not in movement_manager.wants_to_move_char
    mock_event_manager.release_controls.assert_called_once()
    mock_npc.cancel_movement.assert_called_once()


def test_unlock_controls_starts_movement_if_pending(
    movement_manager, mock_npc
):
    movement_manager.wants_to_move_char["npc_1"] = Direction.DOWN
    movement_manager.unlock_controls(mock_npc)
    assert "npc_1" in movement_manager.allow_char_movement
    mock_npc.set_move_direction.assert_called_once_with(Direction.DOWN)


def test_unlock_controls_no_pending_movement(movement_manager, mock_npc):
    movement_manager.unlock_controls(mock_npc)
    assert "npc_1" in movement_manager.allow_char_movement
    mock_npc.set_move_direction.assert_not_called()


def test_lock_controls(movement_manager, mock_npc):
    movement_manager.allow_char_movement.add("npc_1")
    movement_manager.lock_controls(mock_npc)
    assert "npc_1" not in movement_manager.allow_char_movement


def test_stop_and_reset_char(movement_manager, mock_npc, mock_event_manager):
    movement_manager.wants_to_move_char["npc_1"] = Direction.RIGHT
    movement_manager.stop_and_reset_char(mock_npc)
    assert "npc_1" not in movement_manager.wants_to_move_char
    mock_event_manager.release_controls.assert_called_once()
    mock_npc.abort_movement.assert_called_once()


@pytest.mark.parametrize(
    "allowed, expected",
    [
        pytest.param(True, True, id="movement_allowed"),
        pytest.param(False, False, id="movement_not_allowed"),
    ],
)
def test_is_movement_allowed(movement_manager, mock_npc, allowed, expected):
    if allowed:
        movement_manager.allow_char_movement.add("npc_1")

    assert movement_manager.is_movement_allowed(mock_npc) is expected


def test_has_pending_movement(movement_manager, mock_npc):
    assert not movement_manager.has_pending_movement(mock_npc)
    movement_manager.wants_to_move_char["npc_1"] = Direction.UP
    assert movement_manager.has_pending_movement(mock_npc)
    del movement_manager.wants_to_move_char["npc_1"]
    assert not movement_manager.has_pending_movement(mock_npc)
