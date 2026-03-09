# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from types import SimpleNamespace
from unittest.mock import MagicMock

import logging
import pygame as pg
import pytest

from tuxemon.network.client import ConnState, TuxemonClient


@pytest.fixture
def client():
    """Provides a fresh TuxemonClient with a mocked game for each test."""
    game = MagicMock()
    return TuxemonClient(game)


def test_connect_and_disconnect(client):
    client.connection_manager.connect_to_host = MagicMock(return_value=True)
    result = client.connect_to_host("127.0.0.1", 40081)
    assert result is True
    assert client.listening
    assert client.selected_game == ("127.0.0.1", 40081)

    client.disconnect()
    assert not client.listening
    assert client.selected_game is None
    assert client.server_list == []
    assert client.client.registry == {}


def test_disconnect_when_not_listening(client):
    client.listening = False
    client.disconnect()
    assert client.listening is False
    assert client.selected_game is None


def test_registry_property(client):
    client.client.registry = {"abc": {"sprite": "dummy"}}
    assert client.registry == {"abc": {"sprite": "dummy"}}


def test_update_calls_connection_manager_and_dispatcher(client):
    client.connection_manager.update = MagicMock()
    client.client.get_incoming_events = MagicMock(
        return_value=[{"type": "PING"}]
    )
    client.dispatcher.dispatch = MagicMock()

    client.update()

    client.connection_manager.update.assert_called_once()
    client.dispatcher.dispatch.assert_called_once_with({"type": "PING"})


def test_check_notify_dispatches_multiple_events(client):
    client.client.get_incoming_events = MagicMock(
        return_value=[{"type": "PING"}, {"type": "MOVE"}]
    )
    client.dispatcher.dispatch = MagicMock()
    client.check_notify()
    assert client.dispatcher.dispatch.call_count == 2


def test_update_multiplayer_list_delegates(client):
    client.discovery.update_multiplayer_list = MagicMock()
    client.update_multiplayer_list()
    client.discovery.update_multiplayer_list.assert_called_once()


def test_populate_player_delegates(client):
    client.sync_manager.populate_player = MagicMock()
    client.populate_player("PUSH_SELF")
    client.sync_manager.populate_player.assert_called_once_with("PUSH_SELF")


def test_update_player_delegates(client):
    client.sync_manager.update_player = MagicMock()
    client.update_player("north", "CLIENT_MAP_UPDATE")
    client.sync_manager.update_player.assert_called_once_with(
        "north", "CLIENT_MAP_UPDATE"
    )


def test_set_key_condition_delegates(client):
    client.input_translator.translate = MagicMock()
    fake_event = {"key": "up"}
    client.set_key_condition(fake_event)
    client.input_translator.translate.assert_called_once_with(fake_event)


def test_player_interact_delegates(client):
    client.interaction_manager.player_interact = MagicMock()
    sprite = MagicMock()
    client.player_interact(
        sprite, "talk", "CLIENT_INTERACTION", response="hello"
    )
    client.interaction_manager.player_interact.assert_called_once_with(
        sprite, "talk", "CLIENT_INTERACTION", "hello"
    )


def test_route_combat_delegates(client):
    client.interaction_manager.route_combat = MagicMock()
    event = {"combat": True}
    client.route_combat(event)
    client.interaction_manager.route_combat.assert_called_once_with(event)


def test_update_client_map_updates_registry(client):
    sprite = MagicMock()
    client.client.registry["abc"] = {"sprite": sprite}
    event_data = MagicMock()
    event_data.map_name = "forest"
    event_data.char_dict = {"hp": 100}

    import tuxemon.network.client as client_module

    client_module.update_client = MagicMock()

    client.update_client_map("abc", event_data)

    assert client.client.registry["abc"]["map_name"] == "forest"
    client_module.update_client.assert_called_once_with(
        sprite, {"hp": 100}, client.game
    )




def test_update_client_map_places_remote_on_current_map(client):
    sprite = MagicMock()
    client.client.registry["abc"] = {"sprite": sprite}
    client.game.get_map_name.return_value = "forest"
    event_data = MagicMock()
    event_data.map_name = "forest"
    event_data.char_dict = {"hp": 100}

    import tuxemon.network.client as client_module

    client_module.update_client = MagicMock()

    client.update_client_map("abc", event_data)

    client.game.npc_manager.add_npc.assert_called_once_with(sprite)
    client.game.npc_manager.add_npc_off_map.assert_not_called()


def test_update_client_map_places_remote_off_current_map(client):
    sprite = MagicMock()
    client.client.registry["abc"] = {"sprite": sprite}
    client.game.get_map_name.return_value = "forest"
    event_data = MagicMock()
    event_data.map_name = "town"
    event_data.char_dict = {"hp": 100}

    import tuxemon.network.client as client_module

    client_module.update_client = MagicMock()

    client.update_client_map("abc", event_data)

    client.game.npc_manager.add_npc_off_map.assert_called_once_with(sprite)

def test_event_counter_monotonic(client):
    n1 = next(client.event_counter)
    n2 = next(client.event_counter)
    n3 = next(client.event_counter)
    assert n1 < n2 < n3


def test_disconnect_resets_connection_manager(client):
    client.connection_manager.state = ConnState.READY
    client.listening = True
    client.disconnect()
    assert client.connection_manager.state == ConnState.DISCONNECTED


def test_update_client_map_unknown_cuuid(client, caplog):
    event_data = MagicMock()
    event_data.map_name = "forest"
    event_data.char_dict = {"hp": 100}
    client.update_client_map("missing", event_data)
    assert "Unknown client missing" in caplog.text


def test_input_translator_facing_event(client, monkeypatch):
    client.client.send_event = MagicMock()
    client.game.current_state = client.game.get_state_by_name.return_value
    client.game.network_manager.is_connected.return_value = True

    monkeypatch.setattr(
        "tuxemon.network.networking.EventData.from_dict",
        lambda data: MagicMock(to_dict=lambda: data),
    )

    event = MagicMock()
    event.type = pg.KEYDOWN
    event.key = pg.K_UP

    client.set_key_condition(event)

    payload = client.client.send_event.call_args[0][0]
    assert payload["type"] == "CLIENT_FACING"


def test_connection_manager_state_transitions(client, monkeypatch):
    cm = client.connection_manager

    client.client.start_connection = MagicMock()
    client.client._registered = True
    result = cm.connect_to_host("127.0.0.1", 40081)
    assert result is True
    assert cm.state == ConnState.REGISTERING

    fake_player = MagicMock()
    fake_player.__dict__ = {
        "tile_pos": [0, 0],
        "name": "Test",
        "facing": "down",
        "running": False,
        "monsters": [],
        "inventory": [],
    }
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)

    monkeypatch.setattr(
        "tuxemon.network.networking.EventData.from_dict",
        lambda data: MagicMock(to_dict=lambda: data),
    )

    client.client._registered = True
    client.populated = False

    cm.update()
    assert cm.state == ConnState.READY




def test_update_multiplayer_list_includes_local_hosted_server(client):
    server = MagicMock()
    server.listening = True
    server.server_port = 40123
    server.server_name = "My Hosted Server"
    client.game.network_manager.server = server

    client.discovery.update_multiplayer_list()

    assert client.available_games == [("127.0.0.1", 40123)]
    assert client.server_list == ["My Hosted Server (127.0.0.1:40123)"]


def test_update_multiplayer_list_includes_default_server_without_local_host(client):
    server = MagicMock()
    server.listening = False
    client.game.network_manager.server = server

    client.discovery.update_multiplayer_list()

    assert client.available_games == [("127.0.0.1", 40081)]
    assert client.server_list == ["Default Tuxemon Server (127.0.0.1:40081)"]


def test_connection_manager_connects_even_when_running_as_host(client):
    cm = client.connection_manager
    client.client.start_connection = MagicMock()
    client.client._registered = True
    client.game.network_manager.is_host.return_value = True

    result = cm.connect_to_host("127.0.0.1", 40081)

    assert result is True
    client.client.start_connection.assert_called_once_with("127.0.0.1", 40081)
    assert cm.state == ConnState.REGISTERING

def test_interaction_manager_finds_cuuid(client, monkeypatch):
    sprite = MagicMock()
    client.client.registry = {"abc": {"sprite": sprite}}

    fake_player = MagicMock()
    fake_player.__dict__ = {
        "tile_pos": [0, 0],
        "name": "Test",
        "facing": "down",
        "running": False,
        "monsters": [],
        "inventory": [],
    }
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)

    monkeypatch.setattr(
        "tuxemon.network.networking.EventData.from_dict",
        lambda data: MagicMock(to_dict=lambda: data),
    )

    client.client.send_event = MagicMock()

    client.player_interact(sprite, "talk")

    payload = client.client.send_event.call_args[0][0]
    assert payload["target"] == "abc"


def test_connection_manager_stays_registering_until_player_populated(client):
    cm = client.connection_manager
    client.client._registered = True
    client.populated = False
    client.sync_manager.populate_player = MagicMock(return_value=False)
    cm.state = ConnState.REGISTERING

    cm.update()

    assert cm.state == ConnState.REGISTERING


def test_populate_player_handles_uninitialized_map(client, monkeypatch):
    fake_player = MagicMock()
    fake_player.__dict__ = {
        "tile_pos": [0, 0],
        "name": "Test",
        "facing": "down",
    }
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.game.get_map_name.side_effect = ValueError(
        "Name of the map requested when no map is active"
    )
    client.client.send_event = MagicMock()

    result = client.sync_manager.populate_player()

    assert result is False
    client.client.send_event.assert_not_called()


def test_update_player_handles_uninitialized_map(client, monkeypatch):
    fake_player = MagicMock()
    fake_player.__dict__ = {"tile_pos": [3, 4]}
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.game.get_map_name.side_effect = ValueError(
        "Name of the map requested when no map is active"
    )
    client.client.send_event = MagicMock()

    result = client.sync_manager.update_player("down")

    assert result is False
    client.client.send_event.assert_not_called()


def test_update_player_sends_when_initialized(client, monkeypatch):
    fake_player = MagicMock()
    fake_player.__dict__ = {"tile_pos": [3, 4]}
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.game.get_map_name.return_value = "start-town"
    client.client.send_event = MagicMock()

    result = client.sync_manager.update_player("down")

    assert result is True
    payload = client.client.send_event.call_args[0][0]
    assert payload["type"] == "CLIENT_MAP_UPDATE"
    assert payload["map_name"] == "start-town"
    assert payload["char_dict"]["tile_pos"] == (3, 4)


def test_populate_player_sends_running_field(client, monkeypatch):
    fake_player = MagicMock()
    fake_player.__dict__ = {
        "tile_pos": [0, 0],
        "name": "Test",
        "facing": "down",
        "running": True,
        "monsters": [],
        "inventory": [],
    }
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.game.get_map_name.return_value = "start-town"
    client.client.send_event = MagicMock()

    result = client.sync_manager.populate_player()

    assert result is True
    payload = client.client.send_event.call_args[0][0]
    assert payload["char_dict"]["running"] is True


def test_connection_manager_connect_to_host_fails_when_socket_drops(client, monkeypatch):
    cm = client.connection_manager
    client.client.start_connection = MagicMock()
    client.client.disconnect = MagicMock()
    client.client._registered = False
    client.client._last_error = "Connection refused"

    import tuxemon.network.client as client_module

    states = [
        client_module.ConnectionState.CONNECTING,
        client_module.ConnectionState.DISCONNECTED,
    ]

    monkeypatch.setattr(
        type(client.client),
        "state",
        property(
            lambda self: states.pop(0)
            if states
            else client_module.ConnectionState.DISCONNECTED
        ),
    )

    result = cm.connect_to_host("127.0.0.1", 40081)

    assert result is False
    assert cm.state == ConnState.DISCONNECTED
    client.client.disconnect.assert_called_once()
    assert "server-side" in client.last_connection_error




def test_connection_manager_connect_to_host_requires_wallet(client):
    cm = client.connection_manager
    client.game.solana_manager.has_wallet_connection.return_value = False
    client.client.start_connection = MagicMock()

    result = cm.connect_to_host("127.0.0.1", 40081)

    assert result is False
    assert cm.state == ConnState.DISCONNECTED
    assert "Wallet connection required" in client.last_connection_error
    client.client.start_connection.assert_not_called()

def test_connection_manager_diagnose_timeout(client):
    cm = client.connection_manager
    msg = cm._diagnose_failure("10.0.0.2", 40081, "Timed out waiting for registration")
    assert "timed out" in msg.lower()
    assert "10.0.0.2:40081" in msg


def test_connection_manager_diagnose_gateway_refusal(client):
    cm = client.connection_manager
    msg = cm._diagnose_failure(
        "192.168.0.1",
        40081,
        "remote server/network refusal at ws://192.168.0.1:40081: TCP connection refused",
    )
    assert "router/gateway" in msg
    assert "host machine IP" in msg


def test_populate_player_uses_wallet_address_as_default_name(client, monkeypatch):
    client.game.solana_manager.wallet_address = "WalletABC"
    fake_player = MagicMock()
    fake_player.name = "Red"
    fake_player.__dict__ = {
        "tile_pos": [0, 0],
        "name": "Red",
        "facing": "down",
        "running": False,
        "monsters": [],
        "inventory": [],
    }
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.game.get_map_name.return_value = "start-town"
    client.client.send_event = MagicMock()

    result = client.sync_manager.populate_player()

    assert result is True
    payload = client.client.send_event.call_args[0][0]
    assert payload["wallet_address"] == "WalletABC"
    assert payload["char_dict"]["name"] == "WalletABC"


def test_dispatch_client_map_update_populates_unknown_client(client, monkeypatch):
    import tuxemon.network.event_dispatcher as dispatcher_module

    client.update_client_map = MagicMock()
    monkeypatch.setattr(
        dispatcher_module,
        "populate_client",
        MagicMock(return_value=MagicMock()),
    )

    event_dict = {
        "type": "CLIENT_MAP_UPDATE",
        "event_number": 1,
        "cuuid": "new_cuuid",
        "map_name": "start-town",
        "char_dict": {
            "tile_pos": [1, 2],
            "name": "Player",
            "facing": "DOWN",
            "running": False,
            "slug": "player",
            "monsters": [],
            "inventory": [],
        },
    }

    client.dispatcher.dispatch(event_dict)

    dispatcher_module.populate_client.assert_called_once()
    client.update_client_map.assert_called_once()


def test_sync_player_state_if_changed_sends_only_on_change(client, monkeypatch):
    client.listening = True
    client.client._registered = True
    client.client.send_event = MagicMock()
    client.game.get_map_name.return_value = "start-town"
    client.game.solana_manager.wallet_address = "WalletABC"

    fake_money_manager = MagicMock()
    fake_money_manager.get_money.return_value = 123
    fake_money_controller = MagicMock(money_manager=fake_money_manager)

    fake_player = SimpleNamespace(
        tile_pos=[0, 0],
        name="Red",
        facing="down",
        running=False,
        slug="npc_red",
        monsters=[],
        inventory=[],
        money_controller=fake_money_controller,
    )

    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)

    client.sync_manager.sync_player_state_if_changed()
    client.sync_manager.sync_player_state_if_changed()

    assert client.client.send_event.call_count == 1
    payload = client.client.send_event.call_args[0][0]
    assert payload["char_dict"]["money"] == 123
    assert payload["char_dict"]["name"] == "WalletABC"


def test_force_sync_player_state_delegates(client):
    client.sync_manager.force_sync_player_state = MagicMock()

    client.force_sync_player_state()

    client.sync_manager.force_sync_player_state.assert_called_once()


def test_player_sync_manager_force_sync_resets_snapshot(client, monkeypatch):
    client.listening = True
    client.client._registered = True
    client.client.send_event = MagicMock()
    client.game.get_map_name.return_value = "start-town"
    client.game.solana_manager.wallet_address = "WalletABC"

    fake_money_manager = MagicMock()
    fake_money_manager.get_money.return_value = 123
    fake_money_controller = MagicMock(money_manager=fake_money_manager)

    from types import SimpleNamespace

    fake_player = SimpleNamespace(
        tile_pos=[0, 0],
        name="WalletABC",
        facing="down",
        running=False,
        slug="npc_red",
        monsters=[],
        inventory=[],
        money_controller=fake_money_controller,
    )

    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)

    client.sync_manager.sync_player_state_if_changed()
    assert client.client.send_event.call_count == 1

    client.sync_manager.force_sync_player_state()

    assert client.client.send_event.call_count == 2


def test_force_sync_player_state_waits_until_registered(client, monkeypatch):
    client.listening = False
    client.client._registered = False
    client.client.send_event = MagicMock()
    client.game.get_map_name.return_value = "start-town"
    client.game.solana_manager.wallet_address = "WalletABC"

    fake_money_manager = MagicMock()
    fake_money_manager.get_money.return_value = 123
    fake_money_controller = MagicMock(money_manager=fake_money_manager)

    fake_player = SimpleNamespace(
        tile_pos=[0, 0],
        name="WalletABC",
        facing="down",
        running=False,
        slug="npc_red",
        monsters=[],
        inventory=[],
        money_controller=fake_money_controller,
    )

    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)

    client.sync_manager.force_sync_player_state()
    assert client.client.send_event.call_count == 0

    client.listening = True
    client.client._registered = True
    client.sync_manager.sync_player_state_if_changed()

    assert client.client.send_event.call_count == 1


def test_sync_player_state_if_changed_logs_rename_and_map_change(client, monkeypatch, caplog):
    client.listening = True
    client.client._registered = True
    client.client.send_event = MagicMock()
    client.game.get_map_name.return_value = "start-town"
    client.game.solana_manager.wallet_address = "WalletABC"

    fake_money_manager = MagicMock()
    fake_money_manager.get_money.return_value = 1
    fake_money_controller = MagicMock(money_manager=fake_money_manager)

    fake_player = SimpleNamespace(
        tile_pos=[1, 2],
        name="WalletABC",
        facing="down",
        running=False,
        slug="npc_red",
        monsters=[],
        inventory=[],
        money_controller=fake_money_controller,
    )

    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.sync_manager.sync_player_state_if_changed()

    fake_player.name = "Ash"
    client.game.get_map_name.return_value = "desert"
    fake_player.tile_pos = [9, 9]

    with caplog.at_level(logging.WARNING):
        client.sync_manager.sync_player_state_if_changed()

    assert "Local player rename detected before sync" in caplog.text
    assert "Local player map change detected before sync" in caplog.text
    assert "Sent CLIENT_MAP_UPDATE" in caplog.text


def test_force_sync_player_state_logs_when_not_ready(client, monkeypatch, caplog):
    client.listening = False
    client.client._registered = False
    client.client.send_event = MagicMock()
    client.game.get_map_name.return_value = "start-town"
    client.game.solana_manager.wallet_address = "WalletABC"

    fake_money_manager = MagicMock()
    fake_money_manager.get_money.return_value = 1
    fake_money_controller = MagicMock(money_manager=fake_money_manager)

    fake_player = SimpleNamespace(
        tile_pos=[0, 0],
        name="WalletABC",
        facing="down",
        running=False,
        slug="npc_red",
        monsters=[],
        inventory=[],
        money_controller=fake_money_controller,
    )
    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)

    with caplog.at_level(logging.WARNING):
        client.sync_manager.force_sync_player_state()

    assert "Force sync requested for local player state" in caplog.text
    assert "Skipping forced player sync until connection is ready" in caplog.text


def test_sync_player_state_if_changed_logs_party_size_change(client, monkeypatch, caplog):
    class _FakeEventData:
        def __init__(self, payload):
            self.payload = payload

        def to_dict(self):
            return {"char_dict": self.payload["char_dict"]}

    monkeypatch.setattr(
        "tuxemon.network.client.EventData.from_dict",
        lambda payload: _FakeEventData(payload),
    )

    client.listening = True
    client.client._registered = True
    client.client.send_event = MagicMock()
    client.game.get_map_name.return_value = "start-town"
    client.game.solana_manager.wallet_address = "WalletABC"

    fake_money_manager = MagicMock()
    fake_money_manager.get_money.return_value = 1
    fake_money_controller = MagicMock(money_manager=fake_money_manager)

    fake_player = SimpleNamespace(
        tile_pos=[1, 2],
        name="WalletABC",
        facing="down",
        running=False,
        slug="npc_red",
        monsters=[{"slug": "a"}],
        inventory=[],
        money_controller=fake_money_controller,
    )

    monkeypatch.setattr("tuxemon.session.local_session._player", fake_player)
    client.sync_manager.sync_player_state_if_changed()

    fake_player.monsters.append({"slug": "b"})

    with caplog.at_level(logging.WARNING):
        client.sync_manager.sync_player_state_if_changed()

    assert "Local player party size changed before sync" in caplog.text
