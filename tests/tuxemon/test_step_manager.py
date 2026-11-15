# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.entity.steps import StepManager


class DummySession:
    def __init__(self, event_bus):
        self.client = MagicMock()
        self.client.event_bus = event_bus


@pytest.fixture
def mock_event_bus():
    return MagicMock()


@pytest.fixture
def session(mock_event_bus):
    return DummySession(mock_event_bus)


@pytest.fixture
def step_tracker_manager():
    return MagicMock()


@pytest.fixture
def manager(session, step_tracker_manager):
    return StepManager(session, step_tracker_manager, MagicMock())


def test_handle_steps_zero(manager, mock_event_bus):
    manager.handle_steps(
        diff_x=1, diff_y=1, steps_moved=0, monsters_in_party=[]
    )
    mock_event_bus.publish.assert_not_called()


def test_handle_steps_publish(manager, mock_event_bus, session):
    monsters = ["monster1", "monster2"]

    manager.handle_steps(
        diff_x=2, diff_y=3, steps_moved=5, monsters_in_party=monsters
    )

    mock_event_bus.publish.assert_called_once()
    args, kwargs = mock_event_bus.publish.call_args

    assert args[0] == "player_steps_moved"
    assert kwargs["diff_x"] == 2
    assert kwargs["diff_y"] == 3
    assert kwargs["steps"] == 5
    assert kwargs["monsters"] == monsters
    assert kwargs["session"] is session
