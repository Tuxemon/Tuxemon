# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from unittest.mock import MagicMock

import pytest

from tuxemon.network.controller import (
    ControllerServer,
    WebsocketSControllerWrapper,
)
from tuxemon.network.websocket_server import WebsocketServerWrapper
from tuxemon.platform.const import buttons


@pytest.fixture
def controller_server(monkeypatch):
    monkeypatch.setattr(
        WebsocketServerWrapper, "start_listening", lambda self, port: None
    )

    game = MagicMock()
    game.key_events = ()
    game.current_state = MagicMock()
    return ControllerServer(game)


def test_wrapper_starts_listening(monkeypatch):
    mock_start = MagicMock()
    monkeypatch.setattr(WebsocketServerWrapper, "start_listening", mock_start)

    wrapper = WebsocketSControllerWrapper(MagicMock(), 40082)
    wrapper.start_listening()

    mock_start.assert_called_once_with(40082)


def test_wrapper_returns_incoming_events(monkeypatch):
    wrapper = WebsocketSControllerWrapper(MagicMock(), 40082)

    monkeypatch.setattr(
        wrapper.server,
        "get_incoming_events",
        lambda: [("abc", {"type": "KEYDOWN:up"})],
    )

    events = wrapper.get_incoming_events()
    assert events == [("abc", {"type": "KEYDOWN:up"})]


def test_event_number_increments(controller_server):
    assert controller_server.get_next_event_number() == 1
    assert controller_server.get_next_event_number() == 2


def test_net_controller_loop_maps_events(monkeypatch, controller_server):
    monkeypatch.setattr(
        controller_server.server,
        "get_incoming_events",
        lambda: [("abc", {"type": "KEYDOWN:up"})],
    )

    events = controller_server.net_controller_loop()
    assert len(events) == 1
    assert events[0].button == buttons.UP
    assert events[0].value == 1


def test_net_controller_loop_ignores_unknown_events(
    monkeypatch, caplog, controller_server
):
    monkeypatch.setattr(
        controller_server.server,
        "get_incoming_events",
        lambda: [("abc", {"type": "SOMETHING_ELSE"})],
    )

    with caplog.at_level(logging.WARNING):
        events = controller_server.net_controller_loop()

    assert events == []
    assert "Unknown network event" in caplog.text


def test_net_controller_loop_handles_bad_json(
    monkeypatch, caplog, controller_server
):
    monkeypatch.setattr(
        controller_server.server,
        "get_incoming_events",
        lambda: [("abc", "{not valid json}")],
    )

    with caplog.at_level(logging.WARNING):
        events = controller_server.net_controller_loop()

    assert events == []
    assert "Invalid JSON" in caplog.text


def test_net_controller_loop_handles_disconnect(
    monkeypatch, caplog, controller_server
):
    caplog.set_level(logging.INFO, logger="tuxemon.network.controller")

    monkeypatch.setattr(
        controller_server.server,
        "get_incoming_events",
        lambda: [("abc", {"type": "CLIENT_DISCONNECTED"})],
    )

    events = controller_server.net_controller_loop()
    assert events == []
    assert "disconnected" in caplog.text


def test_update_processes_events_into_game(monkeypatch, controller_server):
    monkeypatch.setattr(
        controller_server,
        "net_controller_loop",
        lambda: [MagicMock()],
    )

    controller_server.game.key_events = ()
    controller_server.update()

    assert len(controller_server.game.key_events) == 1
    controller_server.game.current_state.process_event.assert_called_once()
