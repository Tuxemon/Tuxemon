# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Tuxemon server and client."""
from __future__ import annotations

import logging
import pprint
from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, Optional, TypedDict

import pygame as pg

from tuxemon import prepare
from tuxemon.event import get_npc
from tuxemon.middleware import Controller, Multiplayer
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.session import local_session
from tuxemon.states.world import worldstate as world

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

try:
    from neteria.client import NeteriaClient
    from neteria.server import NeteriaServer

    networking = True
except ImportError:
    logger.info("Neteria networking unavailable")
    networking = False

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.platform.events import PlayerInput


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    HOST = "host"
    CLIENT = "client"


class CharDict(TypedDict):
    tile_pos: tuple[int, int]
    name: str
    facing: Literal["front", "back", "left", "right"]


class EventData(TypedDict, total=False):
    type: str
    cuuid: str
    event_number: int
    sprite_name: str
    map_name: str
    char_dict: CharDict
    kb_key: str
    target: str


class NetworkManager:
    def __init__(self, parent: LocalPygameClient) -> None:
        self.parent = parent
        self.server: Optional[TuxemonServer] = None
        self.client: Optional[TuxemonClient] = None
        self.connection_state = ConnectionState.DISCONNECTED

    def initialize(self) -> None:
        self.server = TuxemonServer(self.parent)
        self.client = TuxemonClient(self.parent)

    def update(self, time_delta: float) -> None:
        if self.client and self.client.listening:
            self.client.update(time_delta)
            current_map = self.parent.get_map_name()
            self.parent.npc_manager.add_clients_to_map(
                self.client.client.registry, current_map
            )

        if self.server and self.server.listening:
            self.server.update()

        # Determine current connection state
        if self.server and self.server.listening:
            new_state = ConnectionState.HOST
        elif self.client and self.client.listening:
            new_state = ConnectionState.CLIENT
        else:
            new_state = ConnectionState.DISCONNECTED

        # Update state and log changes
        if new_state != self.connection_state:
            self.connection_state = new_state
            self._log_connection_state()

    def _log_connection_state(self) -> None:
        if self.connection_state == ConnectionState.HOST:
            logger.info("NetworkManager: Host connection just established")
        elif self.connection_state == ConnectionState.CLIENT:
            logger.info("NetworkManager: Client connection just established")
        elif self.connection_state == ConnectionState.DISCONNECTED:
            logger.info("NetworkManager: All connections lost")

    def is_host(self) -> bool:
        return self.connection_state == ConnectionState.HOST

    def is_client(self) -> bool:
        return self.connection_state == ConnectionState.CLIENT

    def is_connected(self) -> bool:
        return self.connection_state in {
            ConnectionState.HOST,
            ConnectionState.CLIENT,
        }


SERVER_NAME = "Default Tuxemon Server"


class TuxemonServer:
    """
    Server class for managing multiplayer games.

    This class sets up and manages a multiplayer server using the Neteria
    networking library. It synchronizes the local game state with all
    connected client states and handles interactions, events, and updates
    between the clients and the server.
    """

    def __init__(
        self,
        game: LocalPygameClient,
        server_name: Optional[str] = SERVER_NAME,
        server_port: int = 40081,
        timeout: int = 15,
    ) -> None:
        """
        Initializes the TuxemonServer instance.

        Parameters:
            game: The instance of the local game client that the server
                will manage.
            server_name: The name of the server as displayed to clients.
                Defaults to "Default Tuxemon Server" if not provided.
            server_port: The port number on which the server listens for
                incoming client connections. Defaults to 40081.
            timeout: The timeout duration (in seconds) for client activity.
                If a client fails to send a ping within this duration, it is
                considered disconnected. Defaults to 15 seconds.
        """
        self.timeout = timeout
        self.game = game
        self.server_name = server_name
        self.server_port = server_port
        self.network_events: list[str] = []
        self.listening = False
        self.interfaces: dict[str, Any] = {}
        self.ips: list[str] = []

        # Handle users without networking support.
        if not networking:
            self.server = DummyNetworking()
            return

        self.server = NeteriaServer(
            Multiplayer(self),
            server_port=self.server_port,
            server_name=self.server_name,
        )

    def update(self) -> Optional[bool]:
        """Updates the server state with information sent from the clients."""
        self.server_timestamp = datetime.now()
        for cuuid in self.server.registry:
            try:
                difference = (
                    self.server_timestamp
                    - self.server.registry[cuuid]["ping_timestamp"]
                )
                if difference.seconds > self.timeout:
                    logger.info(f"Client Disconnected. CUUID: {cuuid}")
                    event_data = EventData(type="CLIENT_DISCONNECTED")
                    self.notify_client(cuuid, event_data)
                    del self.server.registry[cuuid]
                    return False

            except KeyError:
                self.server.registry[cuuid]["ping_timestamp"] = datetime.now()
        return None

    def server_event_handler(self, cuuid: str, event_data: EventData) -> None:
        """
        Handles events sent from the middleware using mapped handlers.

        Parameters:
            cuuid: Client's unique user identification number.
            event_data: Event information sent by client.
        """
        registry = self.server.registry

        # Only respond to the latest message of a given type
        if "event_list" not in registry[cuuid]:
            registry[cuuid]["event_list"] = {}
        elif event_data["type"] not in registry[cuuid]["event_list"]:
            registry[cuuid]["event_list"][event_data["type"]] = -1
        elif (
            event_data["event_number"]
            <= registry[cuuid]["event_list"][event_data["type"]]
        ):
            return
        else:
            registry[cuuid]["event_list"][event_data["type"]] = event_data[
                "event_number"
            ]

        # Mapping event types to their handler methods
        event_handlers = {
            "PUSH_SELF": self.handle_push_self_event,
            "PING": self.handle_ping_event,
            "CLIENT_INTERACTION": self.handle_client_interaction_event,
            "CLIENT_RESPONSE": self.handle_client_response_event,
            "CLIENT_KEYDOWN": self.handle_keydown_event,
            "CLIENT_KEYUP": self.handle_keyup_event,
            "CLIENT_START_BATTLE": self.handle_start_battle_event,
            # Add more mappings here as needed
        }

        # Get the appropriate handler for the event type
        handler = event_handlers.get(event_data["type"])

        if handler:
            # Call the handler method dynamically
            handler(cuuid, event_data)
        else:
            logger.warning(f"Unhandled event type: {event_data['type']}")

    def handle_push_self_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        registry = self.server.registry
        registry[cuuid]["sprite_name"] = event_data["sprite_name"]
        registry[cuuid]["map_name"] = event_data["map_name"]
        registry[cuuid]["char_dict"] = event_data["char_dict"]
        registry[cuuid]["ping_timestamp"] = datetime.now()
        self.notify_populate_client(cuuid, event_data)

    def handle_ping_event(self, cuuid: str, event_data: EventData) -> None:
        registry = self.server.registry
        registry[cuuid]["ping_timestamp"] = datetime.now()

    def handle_client_interaction_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        self.update_char_dict(cuuid, event_data["char_dict"])
        self.notify_client_interaction(cuuid, event_data)

    def handle_client_response_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        self.update_char_dict(cuuid, event_data["char_dict"])
        self.notify_client(cuuid, event_data)

    def handle_keydown_event(self, cuuid: str, event_data: EventData) -> None:
        registry = self.server.registry
        if event_data["kb_key"] == "SHIFT":
            registry[cuuid]["char_dict"]["running"] = True
        elif event_data["kb_key"] == "CTRL":
            pass
        elif event_data["kb_key"] == "ALT":
            pass
        self.notify_client(cuuid, event_data)

    def handle_keyup_event(self, cuuid: str, event_data: EventData) -> None:
        registry = self.server.registry
        if event_data["kb_key"] == "SHIFT":
            registry[cuuid]["char_dict"]["running"] = False
        elif event_data["kb_key"] == "CTRL":
            pass
        elif event_data["kb_key"] == "ALT":
            pass
        self.notify_client(cuuid, event_data)

    def handle_start_battle_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        registry = self.server.registry
        registry[cuuid]["char_dict"]["running"] = False
        self.update_char_dict(cuuid, event_data["char_dict"])
        registry[cuuid]["map_name"] = event_data["map_name"]
        self.notify_client(cuuid, event_data)

    def update_char_dict(self, cuuid: str, char_dict: CharDict) -> None:
        """
        Updates registry with player updates.

        Parameters:
            cuuid: Clients unique user identification number.
            char_dict: character dictionary
        """
        self.server.registry[cuuid]["char_dict"].update(char_dict)

    def notify_client(self, cuuid: str, event_data: EventData) -> None:
        """
        Updates all clients with player updates.

        Parameters:
            cuuid: Clients unique user identification number.
            event_data: Notification flag information.
        """
        event_data["type"] = "NOTIFY_" + event_data["type"]
        event_data["cuuid"] = cuuid
        for client_id in self.server.registry:
            # Don't notify a player that they themselves moved.
            if client_id == cuuid:
                continue

            # Notify client of the players new position.
            elif client_id != cuuid:
                self.send_notification(client_id, event_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Updates all clients with the details of the new client.

        Parameters:
            cuuid: Clients unique user identification number.
            event_data: Event information sent by client.
        """
        event_data["type"] = "NOTIFY_" + event_data["type"]
        event_data_1 = event_data
        for client_id in self.server.registry:
            # Don't notify a player that they themselves populated.
            if client_id == cuuid:
                continue

            elif client_id != cuuid:
                # Send the new client data to this client
                event_data_1["cuuid"] = cuuid
                self.send_notification(client_id, event_data_1)

                # Send this clients data to the new client
                char = self.server.registry[client_id]
                event_data_2 = EventData(
                    type=event_data["type"],
                    cuuid=client_id,
                    event_number=event_data["event_number"],
                    sprite_name=char["sprite_name"],
                    map_name=char["map_name"],
                    char_dict=char["char_dict"],
                )
                self.send_notification(client_id, event_data_2)

    def notify_client_interaction(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Notify a client that another client has interacted with them.

        Parameters:
            cuuid: Clients unique user identification number.
            event_data: Notification information.
        """
        event_data["type"] = "NOTIFY_" + event_data["type"]
        client_id = event_data["target"]
        event_data["target"] = cuuid
        self.send_notification(client_id, event_data)

    def send_notification(self, target_id: str, event_data: EventData) -> None:
        """Helper to send notifications to a specific client."""
        self.server.notify(target_id, event_data)


class ControllerServer:
    """
    Server class for a networked controller.

    Creates a Neteria server to handle network events and passes them
    to the local game for processing.
    """

    def __init__(self, game: LocalPygameClient) -> None:
        """
        Initializes the ControllerServer instance.

        Parameters:
            game: The instance of the local game to be managed.
        """
        self.game = game
        self.network_events: list[str] = []
        self.listening = False
        self.interfaces: dict[str, Any] = {}

        # Handle users without networking support
        if not networking:
            self.server = DummyNetworking()
            return
        self.server = NeteriaServer(Controller(self))

    def update(self) -> None:
        """Updates the server state with information sent from the clients."""
        # Loop through our network events and pass them to the current state.
        controller_events = self.net_controller_loop()
        if controller_events:
            key_events_buffer = list(self.game.key_events)
            for controller_event in controller_events:
                key_events_buffer.append(controller_event)
                if self.game.current_state:
                    self.game.current_state.process_event(controller_event)
            self.game.key_events = tuple(key_events_buffer)

    def net_controller_loop(self) -> Sequence[PlayerInput]:
        """
        Process all network events from controllers and pass them
        down to current State. All network events are converted to keyboard
        events for compatibility.
        """
        event_map = {
            "KEYDOWN:up": PlayerInput(button=buttons.UP, value=1),
            "KEYUP:up": PlayerInput(button=buttons.UP, value=0),
            "KEYDOWN:down": PlayerInput(button=buttons.DOWN, value=1),
            "KEYUP:down": PlayerInput(button=buttons.DOWN, value=0),
            "KEYDOWN:left": PlayerInput(button=buttons.LEFT, value=1),
            "KEYUP:left": PlayerInput(button=buttons.LEFT, value=0),
            "KEYDOWN:right": PlayerInput(button=buttons.RIGHT, value=1),
            "KEYUP:right": PlayerInput(button=buttons.RIGHT, value=0),
            "KEYDOWN:enter": PlayerInput(button=buttons.A, value=1),
            "KEYUP:enter": PlayerInput(button=buttons.A, value=0),
            "KEYDOWN:esc": PlayerInput(button=buttons.BACK, value=1),
            "KEYUP:esc": PlayerInput(button=buttons.BACK, value=0),
        }
        events = []
        for event_data in self.network_events:
            event = event_map.get(event_data)
            if event:
                events.append(event)
            else:
                logger.warning(f"Unknown network event: {event_data}")

        # Clear out the network events list once all events have been processed.
        self.network_events = []
        return events


class TuxemonClient:
    """
    Client class for multiplayer games. Creates a Neteria client and
    synchronizes the local game with the host state.
    """

    def __init__(
        self,
        game: LocalPygameClient,
        server_port: int = 40081,
        wait_delay: float = 0.25,
        ping_time: float = 2.0,
        join_self: bool = False,
    ) -> None:
        """
        Initializes the TuxemonClient instance.

        Parameters:
            game: The instance of the local game client that the client
                will manage.
            server_port: The port number of the server the client will
                connect to. Defaults to 40081.
            wait_delay: The delay (in seconds) used in the autodiscover
                broadcast. Defaults to 0.25 seconds.
            ping_time: The interval (in seconds) at which the client sends
                pings to the server to maintain the connection.
                Defaults to 2.0 seconds.
            join_self: Boolean flag for testing on a single device. If True,
                enables the client to join itself. Defaults to False.
        """
        self.game = game
        self.server_port = server_port
        self.wait_delay = wait_delay
        self.ping_time = ping_time
        self.join_self = join_self

        # tuple = (ip, port)
        self.available_games: list[tuple[str, int]] = []
        self.server_list: list[str] = []
        self.selected_game = None
        self.enable_join_multiplayer = False
        self.wait_broadcast = 0.0  # Used to delay autodiscover broadcast.
        self.populated = False
        self.listening = False
        self.event_list: dict[str, int] = {}

        # Handle users without networking support.
        if not networking:
            self.client = DummyNetworking()
            return

        self.client = NeteriaClient(server_port=self.server_port)
        self.client.registry = {}

    def update(self, time_delta: float) -> None:
        """
        Updates the client and local game state with information sent from the server.

        Parameters:
            time_delta: Time since last frame.
        """
        if self.enable_join_multiplayer:
            self.join_multiplayer(time_delta)

        if self.client.registered and not self.populated:
            self.game.network_manager.connection_state = ConnectionState.CLIENT
            self.populate_player()

        if self.ping_time >= 2:
            self.ping_time = 0
            self.client_alive()
        else:
            self.ping_time += time_delta

        self.check_notify()

    def check_notify(self) -> None:
        """
        Processes notify events sent by the server and updates the
        local client registry.
        """
        for euuid, event_data in list(self.client.event_notifies.items()):
            event_type = event_data["type"]

            if event_type == "NOTIFY_CLIENT_DISCONNECTED":
                self.handle_client_disconnected(event_data, euuid)

            elif event_type == "NOTIFY_PUSH_SELF":
                self.handle_push_self(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_MOVE_START":
                self.handle_client_move_start(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_MOVE_COMPLETE":
                self.handle_client_move_complete(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_MAP_UPDATE":
                self.update_client_map(event_data["cuuid"], event_data)
                del self.client.event_notifies[euuid]

            elif event_type == "NOTIFY_CLIENT_KEYDOWN":
                self.handle_keydown(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_KEYUP":
                self.handle_keyup(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_FACING":
                self.handle_client_facing(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_INTERACTION":
                self.handle_interaction(event_data, euuid)

            elif event_type == "NOTIFY_CLIENT_START_BATTLE":
                self.handle_client_start_battle(event_data, euuid)

    def handle_client_disconnected(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        del self.client.registry[cuuid]
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} disconnected.")

    def handle_push_self(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        if cuuid not in self.client.registry:
            self.client.registry[str(cuuid)] = {}
        sprite = populate_client(
            cuuid, event_data, self.game, self.client.registry
        )
        update_client(sprite, event_data["char_dict"], self.game)
        del self.client.event_notifies[euuid]
        logger.info(f"Processed PUSH_SELF event for client {cuuid}.")

    def handle_client_move_start(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        direction = event_data["direction"]
        sprite = self.client.registry[cuuid]["sprite"]
        sprite.facing = direction
        for d in sprite.direction:
            sprite.direction[d] = d == direction
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} started moving {direction}.")

    def handle_client_move_complete(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        sprite = self.client.registry[cuuid]["sprite"]
        sprite.final_move_dest = event_data["char_dict"]["tile_pos"]
        for d in sprite.direction:
            sprite.direction[d] = False
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} completed their move.")

    def handle_keydown(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        sprite = self.client.registry[cuuid]["sprite"]
        kb_key = event_data["kb_key"]
        if kb_key == "SHIFT":
            sprite.running = True
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} pressed {kb_key}.")

    def handle_keyup(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        sprite = self.client.registry[cuuid]["sprite"]
        kb_key = event_data["kb_key"]
        if kb_key == "SHIFT":
            sprite.running = False
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} released {kb_key}.")

    def handle_client_facing(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        sprite = self.client.registry[cuuid]["sprite"]
        if not sprite.moving:
            sprite.facing = event_data["char_dict"]["facing"]
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} updated facing direction.")

    def handle_interaction(self, event_data: Any, euuid: str) -> None:
        _world = self.game.get_state_by_name(world.WorldState)
        _world.handle_interaction(event_data, self.client.registry)
        del self.client.event_notifies[euuid]
        logger.info(f"Processed interaction for client {event_data['cuuid']}.")

    def handle_client_start_battle(self, event_data: Any, euuid: str) -> None:
        cuuid = event_data["cuuid"]
        sprite = self.client.registry[cuuid]["sprite"]
        sprite.running = False
        sprite.final_move_dest = event_data["char_dict"]["tile_pos"]
        for d in sprite.direction:
            sprite.direction[d] = False
        del self.client.event_notifies[euuid]
        logger.info(f"Client {cuuid} started a battle.")

    def join_multiplayer(self, time_delta: float) -> Optional[bool]:
        """
        Joins the client to the selected server.

        Parameters:
            time_delta: Time since last frame.
        """
        # Prevent joining another game if the client is hosting
        if self.game.network_manager.is_host():
            logger.info("Cannot join multiplayer while hosting a game.")
            self.enable_join_multiplayer = False
            return False

        # Stop attempts if the client is already registered with a server
        if self.client.registered:
            logger.info("Client already registered with a server.")
            self.enable_join_multiplayer = False
            return False

        # Attempt to join the selected server if one is chosen
        if self.selected_game:
            logger.info(f"Joining selected server: {self.selected_game}")
            self.client.register(self.selected_game)

        # Periodically send discovery packets to find servers on the local network
        if self.wait_broadcast >= self.wait_delay:
            logger.info("Sending server discovery packet.")
            self.update_multiplayer_list()
            self.wait_broadcast = 0.0
        else:
            self.wait_broadcast += time_delta
            logger.debug(
                f"Broadcast wait timer updated: {self.wait_broadcast:.2f}"
            )

        return None

    def update_multiplayer_list(self) -> Optional[bool]:
        """
        This method sends a broadcast to detect servers on the local
        network. When a server responds, the method verifies that the
        detected server is not hosted by the current client (to avoid
        self-joining). It then adds unique servers to `self.available_games`
        and their corresponding names to `self.server_list`.
        """
        self.client.autodiscover(autoregister=False)

        # Logic to prevent joining your own game as a client.
        if self.client.discovered_servers:
            for ip, port in self.client.discovered_servers:
                host = (ip, port)

                # Safely retrieve the host name from discovered servers
                host_name = self.client.discovered_servers.get(
                    host, [None, None]
                )[1]

                # Check if the detected server is already in available games
                if any(
                    (ipa, porta) == host for ipa, porta in self.available_games
                ):
                    logger.info("Game already in list, skipping.")
                    return False

                # Ensure host_name is a valid string before appending
                if host_name is None:
                    host_name = "Unknown Server"

                # Add the detected server to the available games list
                self.available_games.append(host)
                self.server_list.append(host_name)

        return None

    def populate_player(self, event_type: str = "PUSH_SELF") -> None:
        """Sends client character to the server."""
        if event_type not in self.event_list:
            self.event_list[event_type] = 0
        player_data = local_session.player.__dict__
        map_name = self.game.get_map_name()
        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
            "sprite_name": player_data.get("sprite_name", "Unknown"),
            "map_name": map_name,
            "char_dict": {
                "tile_pos": player_data.get("tile_pos", [0, 0]),
                "name": player_data.get("name", "Unnamed Player"),
                "facing": player_data.get("facing", "down"),
                # Uncomment and include if monsters or inventory are required
                # "monsters": player_data.get("monsters", []),
                # "inventory": player_data.get("inventory", []),
            },
        }
        self.event_list[event_type] += 1
        self.client.event(event_data)
        self.populated = True

    def update_player(
        self,
        direction: str,
        event_type: str = "CLIENT_MAP_UPDATE",
    ) -> None:
        """
        Sends client's current map and location to the server.

        Parameters:
            direction: Facing/Movement direction of clients character.
            event_type: Event type sent to server used for event_legal() and event_execute() functions in middleware.
        """
        if event_type not in self.event_list:
            self.event_list[event_type] = 0
        pd = local_session.player.__dict__
        map_name = self.game.get_map_name()
        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
            "map_name": map_name,
            "direction": direction,
            "char_dict": {"tile_pos": pd["tile_pos"]},
        }
        self.event_list[event_type] += 1
        self.client.event(event_data)

    def set_key_condition(self, event: Any) -> None:
        """
        Sends server information about a key condition being set or that an
        interaction has occurred.

        :param event: Pygame key event.

        :type event: Dictionary
        """
        if self.game.current_state != self.game.get_state_by_name(
            world.WorldState
        ):
            return

        event_type = None
        kb_key = None
        if event.type == pg.KEYDOWN:
            event_type = "CLIENT_KEYDOWN"
            if event.key == pg.K_LSHIFT or event.key == pg.K_RSHIFT:
                kb_key = "SHIFT"
            elif event.key == pg.K_LCTRL or event.key == pg.K_RCTRL:
                kb_key = "CTRL"
            elif event.key == pg.K_LALT or event.key == pg.K_RALT:
                kb_key = "ALT"

            elif event.key == pg.K_UP:
                kb_key = "up"
            elif event.key == pg.K_DOWN:
                kb_key = "down"
            elif event.key == pg.K_LEFT:
                kb_key = "left"
            elif event.key == pg.K_RIGHT:
                kb_key = "right"

        if event.type == pg.KEYUP:
            event_type = "CLIENT_KEYUP"
            if event.key == pg.K_LSHIFT or event.key == pg.K_RSHIFT:
                kb_key = "SHIFT"
            elif event.key == pg.K_LCTRL or event.key == pg.K_RCTRL:
                kb_key = "CTRL"
            elif event.key == pg.K_LALT or event.key == pg.K_RALT:
                kb_key = "ALT"

            elif event.key == pg.K_UP:
                kb_key = "up"
            elif event.key == pg.K_DOWN:
                kb_key = "down"
            elif event.key == pg.K_LEFT:
                kb_key = "left"
            elif event.key == pg.K_RIGHT:
                kb_key = "right"

        if (
            kb_key == "up"
            or kb_key == "down"
            or kb_key == "left"
            or kb_key == "right"
        ):
            event_type = "CLIENT_FACING"

        if event_type not in self.event_list:
            assert event_type
            self.event_list[event_type] = 0

        if event_type and kb_key:
            if event_type == "CLIENT_FACING":
                if self.game.network_manager.is_connected():
                    event_data = {
                        "type": event_type,
                        "event_number": self.event_list[event_type],
                        "char_dict": {"facing": kb_key},
                    }
                    self.event_list[event_type] += 1
                    self.client.event(event_data)

            elif (
                event_type == "CLIENT_KEYUP" or event_type == "CLIENT_KEYDOWN"
            ):
                event_data = {
                    "type": event_type,
                    "event_number": self.event_list[event_type],
                    "kb_key": kb_key,
                }
                self.event_list[event_type] += 1
                self.client.event(event_data)

    def update_client_map(self, cuuid: str, event_data: Any) -> None:
        """
        Updates client's current map and location to reflect the server registry.

        Parameters:
            cuuid: Clients unique user identification number.
            event_data: Client characters current variable values.
        """
        sprite = self.client.registry[cuuid]["sprite"]
        self.client.registry[cuuid]["map_name"] = event_data["map_name"]
        update_client(sprite, event_data["char_dict"], self.game)

    def player_interact(
        self,
        sprite: NPC,
        interaction: str,
        event_type: str = "CLIENT_INTERACTION",
        response: Any = None,
    ) -> None:
        """
        Sends client to client interaction request to the server.

        Parameters:
            sprite: The character sprite that the player is interacting with.
                Used to identify the target client.
            interaction: The type of interaction being performed (e.g., "TALK",
                "TRADE", "BATTLE").
            event_type: The type of event being triggered.
                Defaults to "CLIENT_INTERACTION".
            response: Additional data or feedback from the interaction, if
                applicable. Defaults to None.
        """
        if event_type not in self.event_list:
            self.event_list[event_type] = 1

        cuuid = None
        for client_id in self.client.registry:
            if self.client.registry[client_id]["sprite"] == sprite:
                cuuid = client_id
                break

        pd = local_session.player.__dict__

        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
            "interaction": interaction,
            "target": cuuid,
            "response": response,
            "char_dict": {
                "monsters": pd.get("monsters", []),
                "inventory": pd.get("inventory", []),
            },
        }
        self.event_list[event_type] += 1
        self.client.event(event_data)

    def route_combat(self, event: Any) -> None:
        logger.debug(event)

    def client_alive(self) -> None:
        """Sends server a ping to let it know that it is still alive."""
        event_type = "PING"
        if event_type not in self.event_list:
            self.event_list[event_type] = 1
        else:
            self.event_list[event_type] += 1

        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
        }

        self.client.event(event_data)


class DummyNetworking:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """The dummy networking object is used when networking is not supported."""
        self.registry: dict[str, Any] = {}
        self.registered = False
        # {(ip, port): (client_version_number, server_name)
        self.discovered_servers: dict[tuple[str, int], tuple[int, str]] = {}
        self.event_notifies: dict[str, Any] = {}

    def event(self, *args: Any, **kwargs: Any) -> None:
        pass

    def listen(self, *args: Any, **kwargs: Any) -> None:
        pass

    def autodiscover(self, *args: Any, **kwargs: Any) -> None:
        pass

    def register(self, *args: Any, **kwargs: Any) -> None:
        pass

    def notify(self, *args: Any, **kwargs: Any) -> None:
        pass


# Universal functions
def populate_client(
    cuuid: Any, event_data: Any, game: LocalPygameClient, registry: Any
) -> Any:
    """
    Creates an NPC to represent the client character and adds the information
    to the registry.

    Parameters:
        cuuid (str): The unique user identification number for the client.
        event_data (Dict[str, Any]): Event information sent by the client,
            containing details about the client character (e.g., sprite name,
            map name, and character dictionary).
        game: The game control object for managing the server or
            client.
        registry (Dict[str, Dict[str, Any]]): A registry containing client
            information on the server or client.

    Returns:
        The sprite representing the client character.
    """
    # TODO: move NPC from actions make make a common core class
    # needs to use actions, or update classes
    raise NotImplementedError

    char_dict = event_data["char_dict"]
    sprite_name = str(event_data["sprite_name"])
    char_name = str(char_dict["name"])
    tile_pos_x = int(char_dict["tile_pos"][0])
    tile_pos_y = int(char_dict["tile_pos"][1])

    # Create the NPC sprite based on the provided information
    game.event_engine.execute_action(
        "create_npc", ["char_name", "tile_pos_x", "tile_pos_y"]
    )
    sprite = get_npc(local_session, "char_name")
    assert sprite
    sprite.isplayer = True
    sprite.final_move_dest = sprite.tile_pos
    sprite.interactions = ["TRADE", "DUEL"]

    # Update the registry with the client sprite and map name
    registry[cuuid]["sprite"] = sprite
    registry[cuuid]["map_name"] = event_data["map_name"]

    return sprite


def update_client(
    sprite: Any, char_dict: Any, game: LocalPygameClient
) -> None:
    """Corrects character location when it changes map or loses sync.

    Updates a client's character information, correcting its location and
    synchronization when switching maps or when data becomes out of sync.

    Parameters:
        sprite: The NPC object representing the local client's character
            (stored in the registry).
        char_dict (dict[str, Any]): A dictionary containing the updated variable values
            for the character (e.g., tile position, state changes).
        game: The game control object (server or client) for managing the game's state.
    """
    # Functionality is incomplete due to lack of global x/y implementation
    return

    # Get the game world state
    world = game.get_state_by_name(world.WorldState)

    # Update sprite attributes based on the character dictionary
    for item, value in char_dict.items():
        sprite.__dict__[item] = value

        # Handle tile position updates
        if item == "tile_pos":
            tile_size = prepare.TILE_SIZE  # Access predefined tile size
            position = [
                char_dict["tile_pos"][0] * tile_size[0],
                char_dict["tile_pos"][1] * tile_size[1],
            ]
            global_x = world.global_x  # Placeholder global x offset
            global_y = world.global_y  # Placeholder global y offset
            abs_position = [
                position[0] + global_x,
                position[1] + (global_y - tile_size[1]),
            ]
            sprite.__dict__["position"] = abs_position
