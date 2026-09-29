# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from enum import Enum, auto
from itertools import count
from typing import TYPE_CHECKING, Any, TypedDict

import pygame as pg

from tuxemon.entity.npc import NPC
from tuxemon.network.event_dispatcher import EventDispatcher
from tuxemon.network.networking import EventData, update_client
from tuxemon.network.websocket_client import WebsocketClientWrapper
from tuxemon.session import local_session
from tuxemon.states import world_state as world

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


class GameEntry(TypedDict):
    ip: str
    port: int
    name: str


class ConnState(Enum):
    DISCONNECTED = auto()
    REGISTERING = auto()
    READY = auto()


class TuxemonClient:
    """Manages multiplayer networking and synchronization for a local game client."""

    def __init__(
        self,
        game: BaseClient,
        server_port: int = 40081,
    ) -> None:
        """
        Initializes the client with networking, event handling, and multiplayer
        support.
        """
        self.game = game
        self.server_port = server_port

        self.dispatcher = EventDispatcher(self)
        self.input_translator = InputEventTranslator(self)
        self.sync_manager = PlayerSyncManager(self)
        self.discovery = MultiplayerDiscovery(self)
        self.interaction_manager = InteractionManager(self)
        self.connection_manager = ConnectionManager(self)

        self.available_games: list[tuple[str, int]] = []
        self.server_list: list[str] = []
        self.selected_game: tuple[str, int] | None = None

        self.populated: bool = False
        self.listening: bool = False
        self.event_counter = count(start=1)

        # Networking wrapper: handles loop, JSON, ping.
        self.client = WebsocketClientWrapper(
            port=self.server_port,
            ping_interval=2.0,
        )

    @property
    def registry(self) -> dict[str, Any]:
        return self.client.registry

    def send_event(self, event_data: dict[str, Any]) -> None:
        """Helper to send a high-level event dict over the network."""
        self.client.send_event(event_data)

    def connect_to_host(self, ip_address: str, port: int) -> None:
        """
        Sets up the client to attempt connection to a specified host/port
        and kicks off connection immediately.
        """
        self.selected_game = (ip_address, port)
        self.listening = True
        self.connection_manager.connect_to_host(ip_address, port)

    def disconnect(self) -> None:
        """Closes the client connection and resets its state."""
        if not self.listening:
            return

        self.client.disconnect()
        self.connection_manager.disconnect()
        self.listening = False
        self.selected_game = None
        self.client.registry = {}
        self.server_list = []
        self.populated = False

    def update(self) -> None:
        """Synchronizes game state and handles connection updates per frame."""
        self.connection_manager.update()
        self.check_notify()

    def check_notify(self) -> None:
        """Dispatches incoming server events to appropriate handlers."""
        for event_dict in self.client.get_incoming_events():
            self.dispatcher.dispatch(event_dict)

    def update_multiplayer_list(self) -> None:
        """Refreshes the list of available multiplayer servers."""
        self.discovery.update_multiplayer_list()

    def populate_player(self, event_type: str = "PUSH_SELF") -> None:
        """Sends the local player's character data to the server."""
        self.sync_manager.populate_player(event_type)

    def update_player(
        self,
        direction: str,
        event_type: str = "CLIENT_MAP_UPDATE",
    ) -> None:
        """Updates the server with the player's current map and position."""
        self.sync_manager.update_player(direction, event_type)

    def set_key_condition(self, event: Any) -> None:
        """Translates input events into network events."""
        payload = self.input_translator.translate(event)
        if payload is not None:
            self.send_event(payload)

    def update_client_map(self, cuuid: str, event_data: EventData) -> None:
        """Updates a remote client's map and character state from server data."""
        entry = self.client.registry.get(cuuid)
        if not entry:
            logger.warning(f"Unknown client {cuuid} in CLIENT_MAP_UPDATE")
            return
        sprite = entry["sprite"]
        self.client.registry[cuuid]["map_name"] = event_data.map_name
        update_client(sprite, event_data.char_dict, self.game)

    def player_interact(
        self,
        sprite: NPC,
        interaction: str,
        event_type: str = "CLIENT_INTERACTION",
        response: Any = None,
    ) -> None:
        """
        Sends an interaction event between the player and another character.
        """
        self.interaction_manager.player_interact(
            sprite, interaction, event_type, response
        )

    def route_combat(self, event: Any) -> None:
        """Handles routing of combat-related events."""
        self.interaction_manager.route_combat(event)


class InputEventTranslator:
    """
    Pure translator: converts pygame events into high-level network event dicts.
    It does NOT perform any sending; that is the caller's responsibility.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client

    def translate(self, event: Any) -> dict[str, Any] | None:
        """
        Returns a dict ready to be sent over the network via
        TuxemonClient.send_event, or None if no event should be sent.
        """
        if (
            self.client.game.current_state
            != self.client.game.get_state_by_name(world.WorldState)
        ):
            logger.debug("Input ignored: not in WorldState.")
            return None

        event_type: str | None = None
        kb_key: str | None = None

        if event.type == pg.KEYDOWN:
            event_type = "CLIENT_KEYDOWN"
            kb_key = self._map_key(event.key)
        elif event.type == pg.KEYUP:
            event_type = "CLIENT_KEYUP"
            kb_key = self._map_key(event.key)

        if event.type == pg.KEYDOWN and kb_key in {
            "up",
            "down",
            "left",
            "right",
        }:
            event_type = "CLIENT_FACING"

        logger.debug(f"Translated input: type={event_type}, key={kb_key}")

        if not event_type or not kb_key:
            return None

        event_data_dict: dict[str, Any] = {
            "type": event_type,
            "event_number": next(self.client.event_counter),
        }

        if event_type == "CLIENT_FACING":
            if self.client.game.network_manager.is_connected():
                event_data_dict["char_dict"] = {"facing": kb_key}
            else:
                return None
        else:
            event_data_dict["kb_key"] = kb_key

        return EventData.from_dict(event_data_dict).to_dict()

    def _map_key(self, key: int) -> str | None:
        key_map = {
            pg.K_LSHIFT: "SHIFT",
            pg.K_RSHIFT: "SHIFT",
            pg.K_LCTRL: "CTRL",
            pg.K_RCTRL: "CTRL",
            pg.K_LALT: "ALT",
            pg.K_RALT: "ALT",
            pg.K_UP: "up",
            pg.K_DOWN: "down",
            pg.K_LEFT: "left",
            pg.K_RIGHT: "right",
        }
        return key_map.get(key)


class PlayerSyncManager:
    """
    Handles synchronization of the local player's state with the server.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client
        self.game = client.game

    def _send_event(self, event_type: str, **fields: Any) -> None:
        """
        Helper for building and sending typed events with an incrementing
        event_number. Centralizes the boilerplate.
        """
        payload: dict[str, Any] = {
            "type": event_type,
            "event_number": next(self.client.event_counter),
        }
        payload.update(fields)
        event_data_obj = EventData.from_dict(payload)
        self.client.send_event(event_data_obj.to_dict())

    def populate_player(self, event_type: str = "PUSH_SELF") -> None:
        """Sends client character to the server."""
        player_data = local_session.player.__dict__
        map_name = self.game.get_map_name()

        char_dict = {
            "tile_pos": player_data.get("tile_pos", [0, 0]),
            "name": player_data.get("name", "Unnamed Player"),
            "facing": player_data.get("facing", "down"),
        }

        self._send_event(
            event_type,
            map_name=map_name,
            char_dict=char_dict,
        )
        self.client.populated = True

    def update_player(
        self, direction: str, event_type: str = "CLIENT_MAP_UPDATE"
    ) -> None:
        """Sends client's current map and location to the server."""
        pd = local_session.player.__dict__
        map_name = self.game.get_map_name()

        char_dict = {"tile_pos": pd["tile_pos"]}

        self._send_event(
            event_type,
            map_name=map_name,
            direction=direction,
            char_dict=char_dict,
        )


class MultiplayerDiscovery:
    """
    Handles discovery and listing of available multiplayer game servers.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client

    def update_multiplayer_list(self) -> None:
        """
        Populates the list of available games with hardcoded entries.
        Replace with real API call when matchmaking backend is ready.
        """
        try:
            games: list[GameEntry] = [
                {
                    "ip": "127.0.0.1",
                    "port": 40081,
                    "name": "Local Test Server",
                },
                {
                    "ip": "192.168.1.50",
                    "port": 40081,
                    "name": "LAN Party Server",
                },
            ]
            self.client.available_games = [
                (str(entry["ip"]), int(entry["port"])) for entry in games
            ]
            self.client.server_list = [str(entry["name"]) for entry in games]
        except Exception as e:
            logger.warning(f"Failed to populate server list: {e}")
            self.client.available_games = []
            self.client.server_list = []


class InteractionManager:
    """
    Handles player-to-player interactions and combat routing.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client
        self.game = client.game

    def player_interact(
        self,
        sprite: NPC,
        interaction: str,
        event_type: str = "CLIENT_INTERACTION",
        response: Any = None,
    ) -> None:
        """
        Sends client-to-client interaction request to the server.
        """
        cuuid: str | None = None
        for client_id, data in self.client.registry.items():
            if data.get("sprite") == sprite:
                cuuid = client_id
                break

        pd = local_session.player.__dict__

        event_data = {
            "type": event_type,
            "event_number": next(self.client.event_counter),
            "interaction": interaction,
            "target": cuuid,
            "response": response,
            "char_dict": {
                "monsters": pd.get("monsters", []),
                "inventory": pd.get("inventory", []),
            },
        }

        self.client.send_event(EventData.from_dict(event_data).to_dict())

    def route_combat(self, event: Any) -> None:
        """Handles routing of combat-related events."""
        logger.debug(f"Combat event received: {event}")


class ConnectionManager:
    """
    Minimal connection manager: delegates lifecycle to WebsocketClientWrapper,
    and only coordinates registration and "ready" state for gameplay.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client
        self.state = ConnState.DISCONNECTED

    def update(self) -> None:
        """
        Checks registration state and transitions into READY when the
        underlying WebsocketClientWrapper reports registration.
        """
        if self.state is ConnState.DISCONNECTED:
            return

        if self.state is ConnState.REGISTERING:
            if self.client.client.registered and not self.client.populated:
                self.client.sync_manager.populate_player()
                self.state = ConnState.READY

    def connect_to_host(self, ip: str, port: int) -> None:
        """
        Attempts to connect to the selected multiplayer server immediately.
        """
        if self.client.game.network_manager.is_host():
            logger.info("Skipping client connection: running as host.")
            return

        logger.info(f"Connecting to WS server: {ip}:{port}")
        self.client.client.start_connection(ip, port)
        self.state = ConnState.REGISTERING

    def disconnect(self) -> None:
        self.state = ConnState.DISCONNECTED
