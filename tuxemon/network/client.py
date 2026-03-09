# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import time
from enum import Enum, auto
from itertools import count
from typing import TYPE_CHECKING, Any, TypedDict

import pygame as pg

from tuxemon.entity.npc import NPC
from tuxemon.network.event_dispatcher import EventDispatcher
from tuxemon.network.networking import EventData, update_client
from tuxemon.network.websocket_client import (
    ConnectionState,
    WebsocketClientWrapper,
)
from tuxemon.session import local_session
from tuxemon.states import world_state as world

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


def _facing_member_name(value: Any) -> str:
    """Convert facing value to Direction enum member name expected by EventData."""
    if hasattr(value, "name"):
        return str(value.name)
    return str(value or "down").upper()

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
        self.last_connection_error: str | None = None

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

    def connect_to_host(self, ip_address: str, port: int) -> bool:
        """Attempts immediate connection and returns whether it succeeded."""
        self.selected_game = (ip_address, port)
        connected = self.connection_manager.connect_to_host(ip_address, port)
        self.listening = connected
        if not connected:
            logger.warning("Connection failed to %s:%s", ip_address, port)
        else:
            self.last_connection_error = None
        return connected

    def get_connection_error_message(self) -> str:
        """Returns a user-facing reason for the last failed connection attempt."""
        return self.last_connection_error or "Unknown connection error"

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

    def populate_player(self, event_type: str = "PUSH_SELF") -> bool:
        """Sends the local player's character data to the server."""
        return self.sync_manager.populate_player(event_type)

    def update_player(
        self,
        direction: str,
        event_type: str = "CLIENT_MAP_UPDATE",
    ) -> bool:
        """Updates the server with the player's current map and position."""
        return self.sync_manager.update_player(direction, event_type)

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

    def _wallet_address(self) -> str:
        wallet = str(self.game.solana_manager.wallet_address or "").strip()
        return wallet

    def _resolve_player_name(self, raw_name: Any, wallet: str) -> str:
        name = str(raw_name or "").strip()
        if name.lower() in {"", "red", "unnamed player"} and wallet:
            return wallet
        return name or "Unnamed Player"

    def _build_char_payload(self, player_data: dict[str, Any], wallet: str) -> dict[str, Any]:
        return {
            "tile_pos": player_data.get("tile_pos", [0, 0]),
            "name": self._resolve_player_name(player_data.get("name"), wallet),
            "facing": _facing_member_name(player_data.get("facing", "down")),
            "running": player_data.get("running", False),
            "slug": player_data.get("slug"),
            "monsters": player_data.get("monsters", []),
            "inventory": player_data.get("inventory", []),
        }

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

    def populate_player(self, event_type: str = "PUSH_SELF") -> bool:
        """Sends client character to the server when player/map are ready."""
        try:
            player_data = local_session.player.__dict__
            map_name = self.game.get_map_name()
        except ValueError as e:
            logger.debug(
                f"Skipping player population until game is initialized: {e}"
            )
            return False

        wallet = self._wallet_address()
        char_dict = self._build_char_payload(player_data, wallet)

        payload = {
            "map_name": map_name,
            "char_dict": char_dict,
            "wallet_address": wallet,
        }
        self._send_event(event_type, **payload)
        self.client.populated = True
        return True

    def update_player(
        self, direction: str, event_type: str = "CLIENT_MAP_UPDATE"
    ) -> bool:
        """Sends client's current map and location to the server."""
        try:
            pd = local_session.player.__dict__
            map_name = self.game.get_map_name()
        except ValueError as e:
            logger.debug(
                f"Skipping player update until game is initialized: {e}"
            )
            return False

        wallet = self._wallet_address()
        char_dict = self._build_char_payload(pd, wallet)

        payload = {
            "map_name": map_name,
            "direction": direction,
            "char_dict": char_dict,
            "wallet_address": wallet,
        }
        self._send_event(event_type, **payload)
        return True


class MultiplayerDiscovery:
    """
    Handles discovery and listing of available multiplayer game servers.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client

    def update_multiplayer_list(self) -> None:
        """Refreshes available games, including the local hosted server."""
        games: list[GameEntry] = [
            {
                "ip": "127.0.0.1",
                "port": int(self.client.server_port),
                "name": "Default Tuxemon Server",
            }
        ]

        try:
            server = self.client.game.network_manager.server
            if server and server.listening:
                games[0] = {
                    "ip": "127.0.0.1",
                    "port": int(server.server_port),
                    "name": str(server.server_name or "Local Hosted Server"),
                }
        except Exception as e:
            logger.warning(f"Failed to discover local hosted server: {e}")

        self.client.available_games = [
            (str(entry["ip"]), int(entry["port"])) for entry in games
        ]
        self.client.server_list = [
            f"{entry['name']} ({entry['ip']}:{entry['port']})"
            for entry in games
        ]


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

        wallet = str(self.game.solana_manager.wallet_address or "").strip()

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
            "wallet_address": wallet,
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
                if self.client.sync_manager.populate_player():
                    self.state = ConnState.READY

    @staticmethod
    def _diagnose_failure(ip: str, port: int, raw_error: str) -> str:
        msg = raw_error.strip() if raw_error else "Timed out waiting for registration"
        msg_l = msg.lower()

        ip_l = ip.strip().lower()
        private_gateway = (
            ip_l.startswith("192.168.")
            and ip_l.endswith(".1")
            or ip_l.startswith("10.")
            and ip_l.endswith(".1")
            or ip_l.startswith("172.")
            and ip_l.endswith(".1")
        )

        if "refused" in msg_l:
            side = (
                "server-side" if ip in {"127.0.0.1", "localhost"} else "remote-server/network"
            )
            gateway_hint = (
                " This IP looks like a router/gateway address; use the host machine IP running SolaMon server instead."
                if private_gateway
                else ""
            )
            return (
                f"{side} refusal at {ip}:{port} ({msg}). "
                "Server is not listening on that address/port or blocked by firewall."
                f"{gateway_hint}"
            )
        if "timed out" in msg_l:
            return (
                f"Connection timed out reaching {ip}:{port}. "
                "Likely network/firewall issue or unreachable server host."
            )
        return f"Connection failed for {ip}:{port}: {msg}"

    def connect_to_host(self, ip: str, port: int) -> bool:
        """Attempts to connect to the selected multiplayer server."""
        logger.warning("Connecting to WS server: %s:%s", ip, port)
        self.client.client.start_connection(ip, port)
        self.state = ConnState.REGISTERING

        timeout_s = 3.0
        interval_s = 0.05
        deadline = time.monotonic() + timeout_s
        saw_connect_attempt = False
        while time.monotonic() < deadline:
            ws_state = self.client.client.state
            if ws_state in {ConnectionState.CONNECTING, ConnectionState.CONNECTED}:
                saw_connect_attempt = True

            if self.client.client.registered:
                logger.warning("Connected to WS server: %s:%s", ip, port)
                self.client.last_connection_error = None
                return True

            if saw_connect_attempt and ws_state is ConnectionState.DISCONNECTED:
                break

            time.sleep(interval_s)

        self.state = ConnState.DISCONNECTED
        self.client.client.disconnect()
        err = self.client.client.last_error or "Timed out waiting for registration"
        diagnosis = self._diagnose_failure(ip, port, err)
        self.client.last_connection_error = diagnosis
        logger.warning("Failed to connect to WS server %s:%s (%s)", ip, port, err)
        logger.warning("Connection diagnosis: %s", diagnosis)
        return False

    def disconnect(self) -> None:
        self.state = ConnState.DISCONNECTED
