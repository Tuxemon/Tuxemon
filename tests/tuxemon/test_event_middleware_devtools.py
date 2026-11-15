# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.event.eventmiddleware import DevToolsMiddleware
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput


@pytest.fixture(autouse=True)
def enable_devtools(monkeypatch):
    monkeypatch.setattr("tuxemon.event.eventmiddleware.DEV_TOOLS", True)


@pytest.fixture
def mock_character():
    c = MagicMock()
    c.ignore_collisions = False
    return c


@pytest.fixture
def mock_map_manager():
    m = MagicMock()
    m.current_map = MagicMock()
    return m


@pytest.fixture
def mock_event_manager():
    return MagicMock()


@pytest.fixture
def mock_input_manager():
    return MagicMock()


@pytest.fixture
def mw(
    mock_character, mock_map_manager, mock_event_manager, mock_input_manager
):
    return DevToolsMiddleware(
        mock_character,
        mock_map_manager,
        mock_event_manager,
        mock_input_manager,
    )


def test_noclip_toggle(mw, mock_character):
    event = PlayerInput(
        button=intentions.NOCLIP,
        value=1,
        previous_value=0,
        hold_time=1,
    )
    mw.preprocess(event)
    assert mock_character.ignore_collisions is True


def test_reload_map(mw, mock_map_manager):
    event = PlayerInput(
        button=intentions.RELOAD_MAP,
        value=1,
        previous_value=0,
        hold_time=1,
    )
    mw.preprocess(event)
    mock_map_manager.current_map.reload_tiles.assert_called_once()
