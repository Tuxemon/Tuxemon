# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.teleporter import (
    Teleporter,
    TeleportQueue,
    TeleportRequest,
)


@pytest.fixture
def mock_map_transition():
    return MagicMock()


@pytest.fixture
def mock_npc_manager():
    return MagicMock()


@pytest.fixture
def mock_state_manager():
    mock = MagicMock()
    mock.active_states = ["WorldState", "OtherState"]
    return mock


@pytest.fixture
def teleporter(
    mock_map_transition,
    mock_npc_manager,
    mock_state_manager,
):
    return Teleporter(
        map_transition=mock_map_transition,
        npc_manager=mock_npc_manager,
        state_manager=mock_state_manager,
    )


@pytest.fixture
def mock_character():
    mock = MagicMock()
    mock.slug = "npc_red"
    mock.current_map = "old_map"
    return mock


@pytest.mark.parametrize(
    "items",
    [
        pytest.param([], id="empty_queue"),
        pytest.param([1], id="single_item"),
        pytest.param([1, 2, 3], id="multiple_items"),
    ],
)
def test_teleport_queue_enqueue_dequeue(items):
    queue = TeleportQueue()

    for i in items:
        queue.enqueue(i)

    assert queue.is_empty() == (len(items) == 0)

    for i in items:
        assert queue.dequeue() == i

    assert queue.is_empty()


def test_teleport_queue_peek():
    queue = TeleportQueue()
    queue.enqueue("A")
    queue.enqueue("B")

    assert queue.peek() == "A"
    assert queue.dequeue() == "A"
    assert queue.peek() == "B"


def test_teleport_queue_clear():
    queue = TeleportQueue()
    queue.enqueue(1)
    queue.enqueue(2)
    queue.clear()
    assert queue.is_empty()


def test_prepare_teleport_pushes_state(
    teleporter, mock_state_manager, mock_character
):
    mock_state_manager.active_states = ["WorldState", "OtherState"]
    mock_state_manager.is_in_base_map_state.return_value = True
    teleporter.prepare_teleport(mock_character)
    mock_state_manager.push_state_with_timeout.assert_called_once_with(
        "TeleporterState", 15
    )


def test_prepare_teleport_no_push_when_many_states(
    teleporter, mock_state_manager, mock_character
):
    mock_state_manager.active_states = ["A", "B", "C"]
    mock_state_manager.is_in_base_map_state.return_value = False
    teleporter.prepare_teleport(mock_character)
    mock_state_manager.push_state_with_timeout.assert_not_called()


def test_execute_teleport_calls_teleport_character(teleporter, mock_character):
    request = TeleportRequest(
        char=mock_character,
        mapname="new_map",
        x=3,
        y=4,
        facing=None,
    )
    teleporter.teleport_character = MagicMock()
    teleporter.execute_teleport(mock_character, request)
    teleporter.teleport_character.assert_called_once_with(
        mock_character, "new_map", 3, 4
    )


def test_execute_teleport_sets_facing(teleporter, mock_character):
    request = TeleportRequest(
        char=mock_character,
        mapname="new_map",
        x=3,
        y=4,
        facing="north",
    )
    teleporter.teleport_character = MagicMock()
    teleporter.execute_teleport(mock_character, request)
    mock_character.set_facing.assert_called_once_with("north")


def test_teleport_character_full_flow(
    teleporter, mock_character, mock_npc_manager
):
    teleporter.prepare_teleport = MagicMock()
    teleporter.map_transition.change_map = MagicMock()
    teleporter.teleport_character(mock_character, "map1", 10, 20)
    teleporter.prepare_teleport.assert_called_once_with(mock_character)
    teleporter.map_transition.change_map.assert_called_once_with("map1")
    mock_npc_manager.place_npc_on_map(mock_character, "map1", 10, 20)


def test_handle_next_teleport_executes(teleporter, mock_character):
    req = TeleportRequest(mock_character, "map", 1, 2)
    teleporter.teleport_queue.enqueue(req)
    teleporter.execute_teleport = MagicMock()
    teleporter.handle_next_teleport(mock_character)
    teleporter.execute_teleport.assert_called_once_with(mock_character, req)


def test_handle_next_teleport_empty_queue(teleporter, mock_character):
    teleporter.execute_teleport = MagicMock()
    teleporter.handle_next_teleport(mock_character)
    teleporter.execute_teleport.assert_not_called()
