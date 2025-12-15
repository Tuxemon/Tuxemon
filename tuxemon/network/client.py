# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional, TypedDict

import pygame as pg

from tuxemon.network.networking import (
    ConnectionState,
    EventType,
    populate_client,
    update_client,
)
from tuxemon.network.websocket_client import WebsocketClientWrapper
from tuxemon.npc import NPC
from tuxemon.session import local_session
from tuxemon.states import world_state as world

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.network.networking import EventData

logger = logging.getLogger(__name__)


class GameEntry(TypedDict):
    ip: str
    port: int
    name: str


class TuxemonClient:
    """Manages multiplayer networking and synchronization for a local game client."""

    def __init__(
        self,
        game: BaseClient,
        server_port: int = 40081,
        wait_delay: float = 0.25,
        ping_time: float = 2.0,
    ) -> None:
        """
        Initializes the client with networking, event handling, and multiplayer
        support.
        """
        self.game = game
        self.server_port = server_port
        self.wait_delay = wait_delay
        self.ping_time = ping_time
        self.dispatcher = EventDispatcher(self)
        self.input_translator = InputEventTranslator(self)
        self.sync_manager = PlayerSyncManager(self)
        self.discovery = MultiplayerDiscovery(self)
        self.interaction_manager = InteractionManager(self)
        self.connection_manager = ConnectionManager(self)

        self.available_games: list[tuple[str, int]] = []
        self.server_list: list[str] = []
        self.selected_game: Optional[tuple[str, int]] = None
        self.enable_join_multiplayer = False

        self.populated = False
        self.listening = False
        self.event_list: dict[str, int] = {}

        self.client = WebsocketClientWrapper(port=self.server_port)
        self.client.registry = {}

    @property
    def registry(self) -> dict[str, Any]:
        return self.client.registry

    def update(self, time_delta: float) -> None:
        """Synchronizes game state and handles connection updates per frame."""
        self.connection_manager.update(time_delta)
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
        """Translates and sends input events to the server."""
        self.input_translator.translate(event)

    def update_client_map(self, cuuid: str, event_data: EventData) -> None:
        """Updates a remote client's map and character state from server data."""
        sprite = self.client.registry[cuuid]["sprite"]
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

    def send_ping(self) -> None:
        """Sends a ping to the server to maintain connection activity."""
        self.sync_manager.send_ping()


class EventDispatcher:
    def __init__(self, client: TuxemonClient):
        self.client = client
        self.game = client.game
        self.handlers: dict[EventType, Callable[[EventData, str], None]] = {
            EventType.CLIENT_DISCONNECTED: self.handle_client_disconnected,
            EventType.PUSH_SELF: self.handle_push_self,
            EventType.CLIENT_MOVE_START: self.handle_client_move_start,
            EventType.CLIENT_MOVE_COMPLETE: self.handle_client_move_complete,
            EventType.CLIENT_KEYDOWN: self.handle_keydown,
            EventType.CLIENT_KEYUP: self.handle_keyup,
            EventType.CLIENT_FACING: self.handle_client_facing,
            EventType.CLIENT_INTERACTION: self.handle_interaction,
            EventType.CLIENT_START_BATTLE: self.handle_client_start_battle,
        }

    def dispatch(self, event_dict: dict[str, Any]) -> None:
        try:
            event_data = EventData.from_dict(event_dict)
            event_type_str = event_data.notify_type
            if event_type_str is None:
                logger.warning("Missing notify_type in event data.")
                return
            event_enum = EventType.from_notify(event_type_str)
        except Exception as e:
            logger.warning(f"Failed to process incoming event: {e}")
            return

        if event_enum is None:
            logger.warning(f"Unknown notify type: {event_type_str}")
            logger.debug(f"Raw event data: {event_dict}")
            return

        euuid = "ws-event"

        if event_enum == EventType.CLIENT_MAP_UPDATE:
            if event_data.cuuid is None:
                logger.warning(
                    f"Missing cuuid in CLIENT_MAP_UPDATE event: {euuid}"
                )
                return
            self.client.update_client_map(event_data.cuuid, event_data)
            return

        handler = self.handlers.get(event_enum)
        if handler:
            logger.debug(f"Dispatching {event_enum} for {euuid}")
            handler(event_data, euuid)
        else:
            logger.warning(f"No handler defined for event type: {event_enum}")
            logger.debug(f"Unhandled event payload: {event_data.to_dict()}")

    def handle_client_disconnected(
        self, event_data: EventData, euuid: str
    ) -> None:
        cuuid = event_data.cuuid
        if cuuid is None:
            logger.warning(
                f"Missing cuuid in CLIENT_DISCONNECTED event: {euuid}"
            )
            return

        self.client.registry.pop(cuuid, None)
        logger.info(f"Client {cuuid} disconnected.")

    def handle_push_self(self, event_data: EventData, euuid: str) -> None:
        cuuid = event_data.cuuid
        if cuuid is None:
            logger.warning(f"Missing cuuid in PUSH_SELF event: {euuid}")
            return

        self.client.registry.setdefault(cuuid, {})
        sprite = populate_client(
            cuuid, event_data, self.game, self.client.registry
        )
        update_client(sprite, event_data.char_dict, self.game)
        logger.info(f"Processed PUSH_SELF event for client {cuuid}.")

    def handle_client_move_start(
        self, event_data: EventData, euuid: str
    ) -> None:
        cuuid = event_data.cuuid
        direction = event_data.direction
        if cuuid is None or direction is None:
            logger.warning(f"Missing data in CLIENT_MOVE_START event: {euuid}")
            return

        sprite = self.client.registry.get(cuuid, {}).get("sprite")
        if sprite:
            sprite.facing = direction
            for d in sprite.direction:
                sprite.direction[d] = d == direction
        logger.info(f"Client {cuuid} started moving {direction}.")

    def handle_client_move_complete(
        self, event_data: EventData, euuid: str
    ) -> None:
        cuuid = event_data.cuuid
        if cuuid is None or event_data.char_dict is None:
            logger.warning(
                f"Missing data in CLIENT_MOVE_COMPLETE event: {euuid}"
            )
            return

        sprite = self.client.registry.get(cuuid, {}).get("sprite")
        if sprite:
            sprite.final_move_dest = event_data.char_dict.tile_pos
            for d in sprite.direction:
                sprite.direction[d] = False
        logger.info(f"Client {cuuid} completed their move.")

    def handle_keydown(self, event_data: EventData, euuid: str) -> None:
        cuuid = event_data.cuuid
        kb_key = event_data.kb_key
        if cuuid is None or kb_key is None:
            logger.warning(f"Missing data in CLIENT_KEYDOWN event: {euuid}")
            return

        sprite = self.client.registry.get(cuuid, {}).get("sprite")
        if sprite and kb_key == "SHIFT":
            sprite.running = True
        logger.info(f"Client {cuuid} pressed {kb_key}.")

    def handle_keyup(self, event_data: EventData, euuid: str) -> None:
        cuuid = event_data.cuuid
        kb_key = event_data.kb_key
        if cuuid is None or kb_key is None:
            logger.warning(f"Missing data in CLIENT_KEYUP event: {euuid}")
            return

        sprite = self.client.registry.get(cuuid, {}).get("sprite")
        if sprite and kb_key == "SHIFT":
            sprite.running = False
        logger.info(f"Client {cuuid} released {kb_key}.")

    def handle_client_facing(self, event_data: EventData, euuid: str) -> None:
        cuuid = event_data.cuuid
        if cuuid is None or event_data.char_dict is None:
            logger.warning(f"Missing data in CLIENT_FACING event: {euuid}")
            return

        sprite = self.client.registry.get(cuuid, {}).get("sprite")
        if sprite and not sprite.moving:
            sprite.facing = event_data.char_dict.facing
        logger.info(f"Client {cuuid} updated facing direction.")

    def handle_interaction(self, event_data: EventData, euuid: str) -> None:
        cuuid = event_data.cuuid
        if cuuid is None:
            logger.warning(
                f"Missing cuuid in CLIENT_INTERACTION event: {euuid}"
            )
            return

        world_state = self.game.get_state_by_name(world.WorldState)
        world_state.handle_interaction(event_data, self.client.registry)
        logger.info(f"Processed interaction for client {cuuid}.")

    def handle_client_start_battle(
        self, event_data: EventData, euuid: str
    ) -> None:
        cuuid = event_data.cuuid
        if cuuid is None or event_data.char_dict is None:
            logger.warning(
                f"Missing data in CLIENT_START_BATTLE event: {euuid}"
            )
            return

        sprite = self.client.registry.get(cuuid, {}).get("sprite")
        if sprite:
            sprite.running = False
            sprite.final_move_dest = event_data.char_dict.tile_pos
            for d in sprite.direction:
                sprite.direction[d] = False
        logger.info(f"Client {cuuid} started a battle.")


class InputEventTranslator:
    def __init__(self, client: TuxemonClient):
        self.client = client

    def translate(self, event: Any) -> None:
        if (
            self.client.game.current_state
            != self.client.game.get_state_by_name(world.WorldState)
        ):
            logger.debug("Input ignored: not in WorldState.")
            return

        event_type = None
        kb_key = None

        if event.type == pg.KEYDOWN:
            event_type = "CLIENT_KEYDOWN"
            kb_key = self._map_key(event.key)
        elif event.type == pg.KEYUP:
            event_type = "CLIENT_KEYUP"
            kb_key = self._map_key(event.key)

        if kb_key in {"up", "down", "left", "right"}:
            event_type = "CLIENT_FACING"

        logger.debug(f"Translated input: type={event_type}, key={kb_key}")

        if event_type and kb_key:
            self._send_event(event_type, kb_key)

    def _map_key(self, key: int) -> Optional[str]:
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

    def _send_event(self, event_type: str, kb_key: str) -> None:
        if event_type not in self.client.event_list:
            self.client.event_list[event_type] = 0

        event_data_dict = {
            "type": event_type,
            "event_number": self.client.event_list[event_type],
        }

        if event_type == "CLIENT_FACING":
            if self.client.game.network_manager.is_connected():
                event_data_dict["char_dict"] = {"facing": kb_key}
        else:
            event_data_dict["kb_key"] = kb_key

        event_data_obj = EventData.from_dict(event_data_dict)
        json_data = json.dumps(event_data_obj.to_dict())

        self.client.event_list[event_type] += 1
        self.client.client.send(json_data)


class PlayerSyncManager:
    """
    Handles synchronization of the local player's state with the server.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client
        self.game = client.game

    def populate_player(self, event_type: str = "PUSH_SELF") -> None:
        """Sends client character to the server."""
        if event_type not in self.client.event_list:
            self.client.event_list[event_type] = 0

        player_data = local_session.player.__dict__
        map_name = self.game.get_map_name()

        event_data_dict = {
            "type": event_type,
            "event_number": self.client.event_list[event_type],
            "map_name": map_name,
            "char_dict": {
                "tile_pos": player_data.get("tile_pos", [0, 0]),
                "name": player_data.get("name", "Unnamed Player"),
                "facing": player_data.get("facing", "down"),
            },
        }

        event_data_obj = EventData.from_dict(event_data_dict)
        json_data = json.dumps(event_data_obj.to_dict())

        self.client.event_list[event_type] += 1
        self.client.client.send(json_data)
        self.client.populated = True

    def update_player(
        self, direction: str, event_type: str = "CLIENT_MAP_UPDATE"
    ) -> None:
        """Sends client's current map and location to the server."""
        if event_type not in self.client.event_list:
            self.client.event_list[event_type] = 0

        pd = local_session.player.__dict__
        map_name = self.game.get_map_name()

        event_data_dict = {
            "type": event_type,
            "event_number": self.client.event_list[event_type],
            "map_name": map_name,
            "direction": direction,
            "char_dict": {"tile_pos": pd["tile_pos"]},
        }

        event_data_obj = EventData.from_dict(event_data_dict)
        json_data = json.dumps(event_data_obj.to_dict())

        self.client.event_list[event_type] += 1
        self.client.client.send(json_data)

    def send_ping(self) -> None:
        """Sends server a ping to let it know that it is still alive."""
        event_type = "PING"
        if event_type not in self.client.event_list:
            self.client.event_list[event_type] = 1
        else:
            self.client.event_list[event_type] += 1

        event_data_dict = {
            "type": event_type,
            "event_number": self.client.event_list[event_type],
        }

        event_data_obj = EventData.from_dict(event_data_dict)
        json_data = json.dumps(event_data_obj.to_dict())

        self.client.client.send(json_data)


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

        Parameters:
            sprite: The character sprite that the player is interacting with.
            interaction: The type of interaction being performed
                (e.g., "TALK", "TRADE", "BATTLE").
            event_type: The type of event being triggered.
            response: Additional data or feedback from the interaction,
                if applicable.
        """
        if event_type not in self.client.event_list:
            self.client.event_list[event_type] = 1

        cuuid = None
        for client_id, data in self.client.registry.items():
            if data.get("sprite") == sprite:
                cuuid = client_id
                break

        pd = local_session.player.__dict__

        event_data = {
            "type": event_type,
            "event_number": self.client.event_list[event_type],
            "interaction": interaction,
            "target": cuuid,
            "response": response,
            "char_dict": {
                "monsters": pd.get("monsters", []),
                "inventory": pd.get("inventory", []),
            },
        }

        self.client.event_list[event_type] += 1
        self.client.client.event(event_data)

    def route_combat(self, event: Any) -> None:
        """
        Handles routing of combat-related events.
        """
        logger.debug(f"Combat event received: {event}")


class ConnectionManager:
    """
    Manages connection lifecycle and server communication for multiplayer
    sessions.
    """

    def __init__(self, client: TuxemonClient):
        self.client = client
        self.game = client.game
        self.ping_timer = client.ping_time
        self.retry_timer = 0.0
        self.retry_interval = 5.0  # seconds between retry attempts

    def update(self, time_delta: float) -> None:
        """
        Updates connection state and sends periodic pings.
        """
        if self.client.enable_join_multiplayer:
            self.retry_timer += time_delta
            if self.retry_timer >= self.retry_interval:
                self.retry_timer = 0
                self.retry_join_multiplayer()
        else:
            self.retry_timer = 0

        if self.client.client.registered and not self.client.populated:
            self.game.network_manager.set_state(ConnectionState.CLIENT)
            self.client.sync_manager.populate_player()

        if self.ping_timer >= 2:
            self.ping_timer = 0
            self.client.sync_manager.send_ping()
        else:
            self.ping_timer += time_delta

    def join_multiplayer(self) -> bool:
        """
        Attempts to connect to the selected multiplayer server.
        Returns True if a connection attempt was made, False otherwise.
        """
        if self.game.network_manager.is_host():
            self.client.enable_join_multiplayer = False
            return False

        if self.client.client.registered:
            self.client.enable_join_multiplayer = False
            return False

        if self.client.selected_game:
            ip, port = self.client.selected_game
            logger.info(f"Attempting to connect to WS server: {ip}:{port}")
            self.client.client.start_connection(ip, port)
            self.client.enable_join_multiplayer = False
            return True

        return False

    def retry_join_multiplayer(self) -> None:
        """
        Attempts to reconnect to the server after retry interval has elapsed.
        """
        success = self.join_multiplayer()
        if not success:
            logger.warning("Retry failed — will try again later.")
