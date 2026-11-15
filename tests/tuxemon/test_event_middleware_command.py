# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventmiddleware import WorldCommandMiddleware
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput


@pytest.fixture
def mock_character():
    return MagicMock()


@pytest.fixture
def mock_state_manager():
    return MagicMock()


@pytest.fixture
def mock_input_manager():
    return MagicMock()


@pytest.fixture
def mock_event_manager():
    return MagicMock()


@pytest.fixture
def mock_menu_manager():
    return MagicMock()


@pytest.fixture
def mw(
    mock_character,
    mock_state_manager,
    mock_input_manager,
    mock_event_manager,
    mock_menu_manager,
):
    return WorldCommandMiddleware(
        mock_character,
        mock_state_manager,
        mock_input_manager,
        mock_event_manager,
        mock_menu_manager,
    )


def test_interact_passes_through(mw):
    event = PlayerInput(button=intentions.INTERACT, value=1, hold_time=0)
    assert mw.preprocess(event) is event


def test_world_menu_opens_state(mw, mock_event_manager, mock_state_manager):
    event = PlayerInput(
        button=intentions.WORLD_MENU,
        value=1,
        previous_value=0,
        hold_time=1,
    )

    result = mw.preprocess(event)

    assert result is None
    mock_event_manager.release_controls.assert_called_once()
    mock_state_manager.push_state.assert_called_once()


def test_world_menu_release_passes_through(mw):
    event = PlayerInput(
        button=intentions.WORLD_MENU, value=0, previous_value=0, hold_time=0
    )

    assert mw.preprocess(event) is event
