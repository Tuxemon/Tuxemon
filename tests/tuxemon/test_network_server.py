# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from unittest.mock import MagicMock

import json
import pytest

from tuxemon.network.server import TuxemonServer
from tuxemon.network.websocket_server import WebsocketServerWrapper


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setattr(
        WebsocketServerWrapper, "start_listening", lambda self, port: True
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


def test_start_hosting_sets_listening_and_starts_wrapper(server):
    server.server.start_listening = MagicMock(return_value=True)
    server.listening = False

    result = server.start_hosting()

    assert result is True
    assert server.listening
    server.server.start_listening.assert_called_once_with(server.server_port)


def test_start_hosting_returns_false_when_wrapper_fails(server):
    server.server.start_listening = MagicMock(return_value=False)
    server.listening = False

    result = server.start_hosting()

    assert result is False
    assert server.listening is False


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
    event = MagicMock(
        map_name="forest",
        wallet_address="Wallet123",
        char_dict={
            "name": "Red",
            "tile_pos": [1, 1],
            "facing": "DOWN",
            "running": False,
            "monsters": [],
            "inventory": [],
        },
    )
    server.client_registry.register_client = MagicMock()
    server.client_registry.set_client_data = MagicMock()
    server.notify_populate_client = MagicMock()

    server.notify_populate_client = MagicMock()
    server.handle_push_self_event("abc", event)

    server.client_registry.register_client.assert_called_once_with(
        "abc", "forest", event.char_dict, "Wallet123"
    )
    stored_payload = server.client_registry.set_client_data.call_args_list[-1][0][2]
    assert stored_payload["name"] == "Wallet123"
    server.notify_populate_client.assert_called_once()


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


def test_update_assigns_event_number_when_missing(server):
    server.server.get_incoming_events = MagicMock(
        return_value=[("abc", {"type": "PING"})]
    )
    server.event_router.route_event = MagicMock()

    server.update()

    event_data = server.event_router.route_event.call_args[0][1]
    assert event_data.type.name == "PING"
    assert isinstance(event_data.event_number, int)


def test_update_ignores_non_dict_events(server):
    server.server.get_incoming_events = MagicMock(
        return_value=[("abc", "not-a-dict")]
    )
    server.event_router.route_event = MagicMock()

    server.update()

    server.event_router.route_event.assert_not_called()


def test_handle_push_self_persists_character_state(server, tmp_path, monkeypatch):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {}

    event = MagicMock(
        map_name="forest",
        wallet_address="WalletPersist123",
        char_dict={
            "name": "PlayerOne",
            "tile_pos": [1, 2],
            "facing": "DOWN",
            "running": False,
            "monsters": [],
            "inventory": [],
        },
    )

    server.notify_populate_client = MagicMock()
    server.handle_push_self_event("abc", event)

    assert server.state_file.exists()
    payload = json.loads(server.state_file.read_text(encoding="utf-8"))
    assert "WalletPersist123" in payload
    assert payload["WalletPersist123"]["map_name"] == "forest"


def test_route_event_allows_push_self_for_unregistered_client(server):
    event = MagicMock()
    event.type.value = "PUSH_SELF"
    event.event_number = 1
    server.event_router.handlers["PUSH_SELF"] = MagicMock()

    server.event_router.route_event("new_client", event)

    server.event_router.handlers["PUSH_SELF"].assert_called_once_with(
        "new_client", event
    )


def test_route_event_rejects_non_push_for_unregistered_client(server):
    event = MagicMock()
    event.type.value = "PING"
    event.event_number = 1
    server.event_router.handlers["PING"] = MagicMock()

    server.event_router.route_event("missing", event)

    server.event_router.handlers["PING"].assert_not_called()


def test_handle_push_self_uses_wallet_state_key(server, tmp_path):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {}

    event = MagicMock(
        map_name="forest",
        wallet_address="Wallet123",
        char_dict={
            "name": "Red",
            "tile_pos": [1, 2],
            "facing": "DOWN",
            "running": False,
            "monsters": [],
            "inventory": [],
        },
    )

    server.notify_populate_client = MagicMock()
    server.handle_push_self_event("abc", event)

    payload = json.loads(server.state_file.read_text(encoding="utf-8"))
    assert "Wallet123" in payload
    assert payload["Wallet123"]["char_dict"]["name"] == "Wallet123"


def test_handle_map_update_event_updates_and_notifies(server):
    event = MagicMock(map_name="forest", char_dict={"hp": 1})
    server.client_registry.set_client_data = MagicMock()
    server.update_char_dict = MagicMock()
    server.notify_client = MagicMock()

    server.handle_map_update_event("abc", event)

    server.client_registry.set_client_data.assert_called_once_with("abc", "map_name", "forest")
    server.update_char_dict.assert_called_once_with("abc", {"hp": 1})
    server.notify_client.assert_called_once_with("abc", event)


def test_handle_map_update_event_logs_rename(server, caplog):
    server.client_registry.registry = {
        "abc": {
            "wallet_address": "Wallet123",
            "map_name": "forest",
            "char_dict": {"name": "OldName"},
        }
    }

    event = MagicMock(map_name="forest", char_dict={"name": "NewName"})
    server.update_char_dict = MagicMock()
    server.notify_client = MagicMock()

    with caplog.at_level(logging.WARNING):
        server.handle_map_update_event("abc", event)

    assert "Character rename detected" in caplog.text


def test_update_char_dict_accepts_dict_payload(server):
    server.client_registry.registry = {
        "abc": {
            "char_dict": {"name": "OldName", "running": False},
        }
    }

    server.client_registry.update_char_dict("abc", {"name": "NewName"})

    assert server.client_registry.registry["abc"]["char_dict"]["name"] == "NewName"




def test_update_char_dict_persists_map_and_position_changes(server, tmp_path, caplog):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {
        "WalletXYZ": {
            "cuuid": "abc",
            "wallet_address": "WalletXYZ",
            "map_name": "forest",
            "char_dict": {
                "name": "PlayerOne",
                "tile_pos": [1, 2],
                "facing": "DOWN",
                "running": False,
                "monsters": [],
                "inventory": [],
            },
        }
    }
    server.client_registry.registry = {
        "abc": {
            "wallet_address": "WalletXYZ",
            "map_name": "mountain",
            "char_dict": {
                "name": "PlayerOne",
                "tile_pos": [9, 9],
                "facing": "DOWN",
                "running": False,
                "monsters": [],
                "inventory": [],
            },
        }
    }

    with caplog.at_level(logging.WARNING):
        server.update_char_dict("abc", {"tile_pos": [9, 9]})

    payload = json.loads(server.state_file.read_text(encoding="utf-8"))
    assert payload["WalletXYZ"]["map_name"] == "mountain"
    assert payload["WalletXYZ"]["char_dict"]["tile_pos"] == [9, 9]
    assert "Persisted character map change to characters.json" in caplog.text
    assert "Persisted character position change to characters.json" in caplog.text


def test_handle_map_update_event_persists_partial_payload_using_registry_state(server, tmp_path):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {}
    server.client_registry.registry = {
        "abc": {
            "wallet_address": "Wallet123",
            "map_name": "forest",
            "char_dict": {
                "name": "OldName",
                "tile_pos": [1, 2],
                "facing": "DOWN",
                "running": False,
                "monsters": [],
                "inventory": [],
            },
        }
    }

    event = MagicMock(map_name="desert", char_dict={"name": "NewName"})
    server.notify_client = MagicMock()

    server.handle_map_update_event("abc", event)

    payload = json.loads(server.state_file.read_text(encoding="utf-8"))
    assert payload["Wallet123"]["map_name"] == "desert"
    assert payload["Wallet123"]["char_dict"]["name"] == "NewName"
    assert payload["Wallet123"]["char_dict"]["tile_pos"] == [1, 2]

def test_update_char_dict_persists_renamed_name_to_state_file(server, tmp_path, caplog):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {
        "WalletXYZ": {
            "cuuid": "abc",
            "wallet_address": "WalletXYZ",
            "map_name": "forest",
            "char_dict": {
                "name": "OldName",
                "tile_pos": [1, 2],
                "facing": "DOWN",
                "running": False,
                "monsters": [],
                "inventory": [],
            },
        }
    }
    server.client_registry.registry = {
        "abc": {
            "wallet_address": "WalletXYZ",
            "map_name": "forest",
            "char_dict": {
                "name": "OldName",
                "tile_pos": [1, 2],
                "facing": "DOWN",
                "running": False,
                "monsters": [],
                "inventory": [],
            },
        }
    }

    with caplog.at_level(logging.WARNING):
        server.update_char_dict("abc", {"name": "NewName"})

    payload = json.loads(server.state_file.read_text(encoding="utf-8"))
    assert payload["WalletXYZ"]["char_dict"]["name"] == "NewName"
    assert "Persisted character rename to characters.json" in caplog.text


def test_persist_character_state_accepts_legacy_signature(server, tmp_path):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {}

    char_dict = {
        "name": "LegacyPlayer",
        "tile_pos": [1, 2],
        "facing": "DOWN",
        "running": False,
        "monsters": [],
        "inventory": [],
    }

    server._persist_character_state("abc", "forest", char_dict)

    payload = json.loads(server.state_file.read_text(encoding="utf-8"))
    assert "abc" in payload
    assert payload["abc"]["map_name"] == "forest"
    assert payload["abc"]["char_dict"]["name"] == "LegacyPlayer"


def test_handle_push_self_event_rejects_walletless_clients(server):
    event = MagicMock(
        map_name="forest",
        wallet_address="",
        char_dict={
            "name": "Guest",
            "tile_pos": [1, 1],
            "facing": "DOWN",
            "running": False,
            "monsters": [],
            "inventory": [],
        },
    )
    server.client_registry.register_client = MagicMock()
    server.notify_populate_client = MagicMock()
    server.server.disconnect_client = MagicMock()

    server.handle_push_self_event("abc", event)

    server.client_registry.register_client.assert_not_called()
    server.notify_populate_client.assert_not_called()
    server.server.disconnect_client.assert_called_once_with("abc")


def test_handle_push_self_event_accepts_saved_lowercase_facing(server, tmp_path):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {
        "WalletABC": {
            "cuuid": "old",
            "wallet_address": "WalletABC",
            "map_name": "start_tuxemon.tmx",
            "char_dict": {
                "tile_pos": [2, 3],
                "name": "WalletABC",
                "facing": "down",
                "running": False,
                "slug": "npc_red",
                "monsters": [],
                "inventory": [],
            },
        }
    }

    event = MagicMock(
        map_name="forest",
        wallet_address="WalletABC",
        char_dict={
            "name": "Red",
            "tile_pos": [1, 2],
            "facing": "DOWN",
            "running": False,
            "monsters": [],
            "inventory": [],
        },
    )

    server.notify_populate_client = MagicMock()

    server.handle_push_self_event("abc", event)

    server.notify_populate_client.assert_called_once()
    _, outbound = server.notify_populate_client.call_args[0]
    assert outbound.char_dict["facing"] == "DOWN"


def test_persist_character_state_emits_terminal_log_for_rename_and_party_change(server, tmp_path):
    server.state_dir = tmp_path / "server"
    server.state_file = server.state_dir / "characters.json"
    server.character_state_store = {
        "WalletXYZ": {
            "cuuid": "abc",
            "wallet_address": "WalletXYZ",
            "map_name": "forest",
            "char_dict": {
                "name": "OldName",
                "tile_pos": [1, 2],
                "facing": "DOWN",
                "running": False,
                "monsters": [{"slug": "a"}],
                "inventory": [],
            },
        }
    }
    server.server._emit_terminal_log = MagicMock()

    server._persist_character_state(
        "abc",
        "WalletXYZ",
        "forest",
        {
            "name": "NewName",
            "tile_pos": [1, 2],
            "facing": "DOWN",
            "running": False,
            "monsters": [{"slug": "a"}, {"slug": "b"}],
            "inventory": [],
        },
    )

    emitted_logs = "\n".join(call.args[0] for call in server.server._emit_terminal_log.call_args_list)
    assert "Persisted character rename to characters.json" in emitted_logs
    assert "Persisted party size change to characters.json" in emitted_logs


def test_handle_map_update_event_logs_incoming_party_change_to_terminal(server):
    server.client_registry.registry = {
        "abc": {
            "wallet_address": "Wallet123",
            "map_name": "forest",
            "char_dict": {
                "name": "OldName",
                "tile_pos": [1, 2],
                "facing": "DOWN",
                "running": False,
                "monsters": [{"slug": "a"}],
                "inventory": [],
            },
        }
    }
    server.server._emit_terminal_log = MagicMock()
    event = MagicMock(
        map_name="forest",
        char_dict={
            "name": "OldName",
            "monsters": [{"slug": "a"}, {"slug": "b"}],
        },
    )
    server.update_char_dict = MagicMock()
    server.notify_client = MagicMock()

    server.handle_map_update_event("abc", event)

    emitted_logs = "\n".join(call.args[0] for call in server.server._emit_terminal_log.call_args_list)
    assert "Incoming party size change detected" in emitted_logs
