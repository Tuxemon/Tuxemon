# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.network.server import TuxemonServer
from tuxemon.network.websocket_server import WebsocketServerWrapper


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setattr(
        WebsocketServerWrapper, "start_listening", lambda self, port: None
    )
    game = MagicMock()
    return TuxemonServer(game)


def test_shutdown_clears_registry_and_stops_listening(server):
    server.client_registry.registry = {"abc": {"sprite": "dummy"}}
    server.event_factory.create_event = MagicMock(
        return_value={"type": "CLIENT_DISCONNECTED"}
    )
    server.notify_client = MagicMock()

    server.shutdown()

    assert server.client_registry.registry == {}
    assert not server.listening
    server.notify_client.assert_called()


def test_get_next_event_number_increments(server):
    assert server.get_next_event_number() == 1
    assert server.get_next_event_number() == 2


def test_server_event_handler_routes_event(server):
    event = MagicMock()
    server.event_router.route_event = MagicMock()
    server.server_event_handler("abc", event)
    server.event_router.route_event.assert_called_once_with("abc", event)


def test_handle_client_disconnected_event_removes_and_notifies(server):
    event = MagicMock()
    server.client_registry.remove_client = MagicMock()
    server.notify_client = MagicMock()

    server.handle_client_disconnected_event("abc", event)

    server.client_registry.remove_client.assert_called_once_with("abc")
    server.notify_client.assert_called_once_with("abc", event)


def test_handle_push_self_event_registers_and_notifies(server):
    event = MagicMock(map_name="forest", char_dict={"hp": 100})
    server.client_registry.register_client = MagicMock()
    server.notify_populate_client = MagicMock()

    server.handle_push_self_event("abc", event)

    server.client_registry.register_client.assert_called_once_with(
        "abc", "forest", {"hp": 100}
    )
    server.notify_populate_client.assert_called_once_with("abc", event)


def test_handle_ping_event_updates_timestamp(server):
    event = MagicMock()
    server.client_registry.set_client_data = MagicMock()

    server.handle_ping_event("abc", event)

    server.client_registry.set_client_data.assert_called_once()
    args = server.client_registry.set_client_data.call_args[0]
    assert args[0] == "abc"
    assert args[1] == "ping_timestamp"


def test_handle_client_interaction_event_updates_and_notifies(server):
    event = MagicMock(char_dict={"hp": 50})
    server.update_char_dict = MagicMock()
    server.notify_client_interaction = MagicMock()

    server.handle_client_interaction_event("abc", event)

    server.update_char_dict.assert_called_once_with("abc", {"hp": 50})
    server.notify_client_interaction.assert_called_once_with("abc", event)


def test_handle_client_response_event_updates_and_notifies(server):
    event = MagicMock(char_dict={"hp": 75})
    server.update_char_dict = MagicMock()
    server.notify_client = MagicMock()

    server.handle_client_response_event("abc", event)

    server.update_char_dict.assert_called_once_with("abc", {"hp": 75})
    server.notify_client.assert_called_once_with("abc", event)


def test_handle_key_event_shift_updates_running(server):
    event = MagicMock(kb_key="SHIFT")
    server.client_registry.set_client_data = MagicMock()
    server.notify_client = MagicMock()

    server.handle_key_event("abc", event, True)

    server.client_registry.set_client_data.assert_called_once_with(
        "abc", "char_dict", {"running": True}
    )
    server.notify_client.assert_called_once_with("abc", event)


def test_handle_start_battle_event_updates_and_notifies(server):
    event = MagicMock(map_name="arena", char_dict={"hp": 90})
    server.client_registry.update_char_field = MagicMock()
    server.update_char_dict = MagicMock()
    server.client_registry.set_client_data = MagicMock()
    server.notify_client = MagicMock()

    server.handle_start_battle_event("abc", event)

    server.client_registry.update_char_field.assert_called_once_with(
        "abc", "running", False
    )
    server.update_char_dict.assert_called_once_with("abc", {"hp": 90})
    server.client_registry.set_client_data.assert_called_once_with(
        "abc", "map_name", "arena"
    )
    server.notify_client.assert_called_once_with("abc", event)


def test_notify_methods_delegate(server):
    event = MagicMock()
    server.notification_manager.notify_client = MagicMock()
    server.notification_manager.notify_populate_client = MagicMock()
    server.notification_manager.notify_client_interaction = MagicMock()
    server.notification_manager.send_notification = MagicMock()

    server.notify_client("abc", event)
    server.notify_populate_client("abc", event)
    server.notify_client_interaction("abc", event)
    server.send_notification("target", event)

    server.notification_manager.notify_client.assert_called_once_with(
        "abc", event
    )
    server.notification_manager.notify_populate_client.assert_called_once_with(
        "abc", event
    )
    server.notification_manager.notify_client_interaction.assert_called_once_with(
        "abc", event
    )
    server.notification_manager.send_notification.assert_called_once_with(
        "target", event
    )


def test_update_handles_client_timeout(server):
    server.client_registry.check_timeouts = MagicMock(return_value=["abc"])
    server.event_factory.create_event = MagicMock(
        return_value={"type": "CLIENT_DISCONNECTED"}
    )
    server.server.disconnect_client = MagicMock()
    server.notify_client = MagicMock()
    server.client_registry.remove_client = MagicMock()

    assert server.update() is None

    server.server.disconnect_client.assert_called_once_with("abc")
    server.notify_client.assert_called_once_with(
        "abc", {"type": "CLIENT_DISCONNECTED"}
    )
    server.client_registry.remove_client.assert_called_once_with("abc")
