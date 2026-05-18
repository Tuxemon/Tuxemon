# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from unittest.mock import MagicMock

import pygame as pg
import pytest

from tuxemon.network.client import ConnState, TuxemonClient


@pytest.fixture
def client():
    """Provides a fresh TuxemonClient with a mocked game for each test."""
    game = MagicMock()
    return TuxemonClient(game)


def test_connect_and_disconnect(client):
    client.connect_to_host("127.0.0.1", 40081)
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

    with caplog.at_level(logging.WARNING):
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

    client.game.network_manager.is_host.return_value = False

    cm.connect_to_host("127.0.0.1", 40081)
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
