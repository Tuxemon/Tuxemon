# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from tuxemon.network.networking import EventType
from tuxemon.network.websocket_server import WebsocketServerWrapper


@pytest.fixture
def wrapper():
    game_server = MagicMock()
    game_server.get_next_event_number = MagicMock(side_effect=[1, 2, 3])
    return WebsocketServerWrapper(game_server)


def test_disconnect_client_does_not_remove_registry(wrapper):
    wrapper.loop = MagicMock()
    wrapper.client_registry = {"abc": MagicMock()}
    wrapper.registry = {"abc": {"peer": "1.2.3.4:9999"}}

    wrapper.disconnect_client("abc")

    assert "abc" not in wrapper.client_registry
    assert "abc" in wrapper.registry


def test_handle_disconnect_removes_registry_and_pushes_event(wrapper):
    wrapper.registry = {"abc": {"peer": "1.2.3.4:9999"}}
    wrapper.client_registry = {"abc": MagicMock()}

    wrapper._handle_disconnect("abc", reason="timeout")

    # registry removed here
    assert "abc" not in wrapper.registry
    assert "abc" not in wrapper.client_registry

    cuuid, event = wrapper.incoming_queue.get_nowait()
    assert cuuid == "abc"
    assert event["type"] == EventType.CLIENT_DISCONNECTED.value
    assert event["reason"] == "timeout"


def test_handler_rejects_when_max_clients_reached(wrapper):
    wrapper.max_clients = 1
    wrapper.client_registry = {"existing": MagicMock()}

    websocket = AsyncMock()
    websocket.remote_address = ("1.2.3.4", 9999)
    websocket.recv = AsyncMock(return_value=json.dumps({"cuuid": None}))

    websocket.close = AsyncMock()

    asyncio.run(wrapper._handler(websocket))

    websocket.close.assert_awaited()


def test_handler_registers_new_client(wrapper):
    websocket = AsyncMock()
    websocket.remote_address = ("1.2.3.4", 9999)
    websocket.recv = AsyncMock(return_value=json.dumps({"cuuid": None}))

    websocket.__aiter__.return_value = iter([])

    asyncio.run(wrapper._handler(websocket))

    assert len(wrapper.registry) == 1
    cuuid = list(wrapper.registry.keys())[0]
    assert wrapper.registry[cuuid]["peer"] == "1.2.3.4:9999"


def test_listener_updates_last_message(wrapper):
    wrapper.registry = {
        "abc": {"peer": "x", "connected_at": None, "last_message_at": None}
    }

    websocket = AsyncMock()
    websocket.__aiter__.return_value = iter([json.dumps({"type": "PING"})])

    asyncio.run(wrapper._listen_to_client("abc", websocket))

    assert wrapper.registry["abc"]["last_message_at"] is not None


def test_listener_rejects_invalid_event(wrapper, caplog):
    wrapper.registry = {"abc": {"peer": "x"}}

    websocket = AsyncMock()
    websocket.__aiter__.return_value = iter([json.dumps({"notype": True})])

    with caplog.at_level(logging.WARNING):
        asyncio.run(wrapper._listen_to_client("abc", websocket))

    assert "Invalid event payload" in caplog.text


def test_listener_logs_raw_message_when_debug(wrapper, caplog):
    caplog.set_level(logging.DEBUG, logger="tuxemon.network.websocket_server")
    wrapper.debug = True
    wrapper.registry = {"abc": {"peer": "x"}}

    websocket = AsyncMock()
    websocket.__aiter__.return_value = iter([json.dumps({"type": "PING"})])

    asyncio.run(wrapper._listen_to_client("abc", websocket))

    assert "Raw incoming from abc" in caplog.text


def test_listener_handles_cancelled_error(wrapper, caplog):
    caplog.set_level(logging.INFO, logger="tuxemon.network.websocket_server")
    websocket = AsyncMock()
    websocket.__aiter__.side_effect = asyncio.CancelledError()

    asyncio.run(wrapper._listen_to_client("abc", websocket))

    assert "Listener cancelled for abc" in caplog.text


def test_handler_sets_reason_on_handshake_failure(wrapper, caplog):
    websocket = AsyncMock()
    websocket.remote_address = ("1.2.3.4", 9999)
    websocket.recv = AsyncMock(side_effect=Exception("boom"))

    asyncio.run(wrapper._handler(websocket))

    assert "Handshake failed" in caplog.text

    cuuid, event = wrapper.incoming_queue.get_nowait()
    assert event["reason"] == "handshake_failed"
