# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

from tuxemon.db import Direction
from tuxemon.network.networking import CharData, EventData, EventType
from tuxemon.network.websocket_server import WebsocketServerWrapper

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


SERVER_NAME = "Default Tuxemon Server"


class TuxemonServer:
    """
    Server class for managing multiplayer game state and communication using
    WebSockets.
    """

    def __init__(
        self,
        game: BaseClient,
        server_name: Optional[str] = SERVER_NAME,
        server_port: int = 40081,
        timeout: int = 15,
    ) -> None:
        """
        Initializes the TuxemonServer instance, sets up networking, event routing,
        and client state management.
        """
        self.timeout = timeout
        self.game = game
        self.server_name = server_name
        self.server_port = server_port
        self.network_events: list[str] = []
        self.listening = False
        self.interfaces: dict[str, Any] = {}
        self.ips: list[str] = []
        self._event_counter = 0
        self.server_timestamp: datetime = datetime.now()

        self.server = WebsocketServerWrapper(self)
        self.server.start_listening(self.server_port)
        self.listening = True
        self.client_registry = ClientRegistry(timeout=self.timeout)
        self.event_router = EventRouter(
            self.client_registry.registry, self.get_next_event_number
        )
        self.event_factory = EventFactory(self.get_next_event_number)
        self.notification_manager = NotificationManager(
            self.server, self.get_next_event_number, self.event_factory
        )
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """
        Registers all event handlers with the event router for dispatching
        incoming events to appropriate methods.
        """
        self.event_router.register_handler(
            EventType.PUSH_SELF, self.handle_push_self_event
        )
        self.event_router.register_handler(
            EventType.PING, self.handle_ping_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_INTERACTION, self.handle_client_interaction_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_RESPONSE, self.handle_client_response_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_KEYDOWN,
            lambda c, e: self.handle_key_event(c, e, True),
        )
        self.event_router.register_handler(
            EventType.CLIENT_KEYUP,
            lambda c, e: self.handle_key_event(c, e, False),
        )
        self.event_router.register_handler(
            EventType.CLIENT_START_BATTLE, self.handle_start_battle_event
        )
        self.event_router.register_handler(
            EventType.CLIENT_DISCONNECTED,
            self.handle_client_disconnected_event,
        )

    def get_next_event_number(self) -> int:
        """
        Generates and returns the next unique event number for sequencing
        events.
        """
        self._event_counter += 1
        return self._event_counter

    def update(self) -> Optional[bool]:
        """
        Processes incoming events from clients, routes them to handlers, and
        checks for client timeouts.
        Returns False if a client times out and is disconnected, otherwise None.
        """
        self.server_timestamp = datetime.now()

        for cuuid, event_dict in self.server.get_incoming_events():
            try:
                event_data = EventData.from_dict(event_dict)
                self.server_event_handler(cuuid, event_data)

            except Exception as e:
                logger.error(f"Error handling event from CUUID {cuuid}: {e}")

        for cuuid in self.client_registry.check_timeouts(
            self.server_timestamp
        ):
            logger.info(f"Client Disconnected (Timeout). CUUID: {cuuid}")
            event_data = self.event_factory.create_event(
                EventType.CLIENT_DISCONNECTED, cuuid
            )
            self.server.disconnect_client(cuuid)
            self.notify_client(cuuid, event_data)
            self.client_registry.remove_client(cuuid)
            return False

        return None

    def server_event_handler(self, cuuid: str, event_data: EventData) -> None:
        """
        Delegates an incoming event to the appropriate handler via the
        event router.
        """
        self.event_router.route_event(cuuid, event_data)

    def handle_client_disconnected_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Handles a client disconnection event triggered by the network wrapper
        and notifies other clients.
        """
        self.client_registry.remove_client(cuuid)

        logger.info(
            f"Client Disconnected (Handled by Wrapper). CUUID: {cuuid}"
        )

        self.notify_client(cuuid, event_data)

    def handle_push_self_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Registers a new client or updates an existing one with initial map
        and character data, then notifies others.
        """
        self.client_registry.register_client(
            cuuid, event_data.map_name, event_data.char_dict
        )
        self.notify_populate_client(cuuid, event_data)

    def handle_ping_event(self, cuuid: str, event_data: EventData) -> None:
        """
        Updates the ping timestamp for a client to indicate they are still
        connected.
        """
        self.client_registry.set_client_data(
            cuuid, "ping_timestamp", datetime.now()
        )

    def handle_client_interaction_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Processes a client interaction event, updates character data, and
        notifies the target client.
        """
        self.update_char_dict(cuuid, event_data.char_dict)
        self.notify_client_interaction(cuuid, event_data)

    def handle_client_response_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Handles a response from a client, updates their character data, and
        notifies other clients.
        """
        self.update_char_dict(cuuid, event_data.char_dict)
        self.notify_client(cuuid, event_data)

    def handle_key_event(
        self, cuuid: str, event_data: EventData, pressed: bool
    ) -> None:
        """
        Handles key press or release events (e.g., SHIFT) and updates the
        client's running state accordingly.
        """
        if event_data.kb_key == "SHIFT":
            self.client_registry.set_client_data(
                cuuid, "char_dict", {"running": pressed}
            )
        self.notify_client(cuuid, event_data)

    def handle_start_battle_event(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Handles the start of a battle by updating the client's character state
        and notifying others.
        """
        self.client_registry.update_char_field(cuuid, "running", False)
        self.update_char_dict(cuuid, event_data.char_dict)
        self.client_registry.set_client_data(
            cuuid, "map_name", event_data.map_name
        )
        self.notify_client(cuuid, event_data)

    def update_char_dict(
        self, cuuid: str, char_data: Optional[CharData]
    ) -> None:
        """
        Updates the character dictionary for a client with new data.
        """
        self.client_registry.update_char_dict(cuuid, char_data)

    def notify_client(self, cuuid: str, event_data: EventData) -> None:
        """
        Sends an event notification to all clients except the originator.
        """
        self.notification_manager.notify_client(cuuid, event_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """
        Notifies all clients about a newly joined client and sends existing
        client data to the new client.
        """
        self.notification_manager.notify_populate_client(cuuid, event_data)

    def notify_client_interaction(
        self, cuuid: str, event_data: Optional[EventData]
    ) -> None:
        """
        Notifies a target client that another client has interacted with them.
        Skips if event data is missing.
        """
        if event_data is None:
            logger.warning(
                f"No event data provided for interaction from CUUID: {cuuid}"
            )
            return

        self.notification_manager.notify_client_interaction(cuuid, event_data)

    def send_notification(self, target_id: str, event_data: EventData) -> None:
        """
        Sends a direct event notification to a specific client.
        """
        self.notification_manager.send_notification(target_id, event_data)


class EventRouter:
    """
    Routes incoming EventData to the appropriate handler based on EventType.
    Ensures deduplication and freshness of events.
    """

    def __init__(
        self,
        registry: dict[str, dict[str, Any]],
        get_next_event_number: Callable[[], int],
    ) -> None:
        self.registry = registry
        self.get_next_event_number = get_next_event_number
        self.handlers: dict[str, Callable[[str, EventData], None]] = {}

    def register_handler(
        self, event_type: EventType, handler: Callable[[str, EventData], None]
    ) -> None:
        self.handlers[event_type.value] = handler

    def route_event(self, cuuid: str, event_data: EventData) -> None:
        if cuuid not in self.registry:
            logger.warning(f"CUUID {cuuid} not found in registry.")
            return

        event_list = self.registry[cuuid].setdefault("event_list", {})
        last_event_number = event_list.get(event_data.type, -1)

        if event_data.event_number <= last_event_number:
            return

        event_list[event_data.type] = event_data.event_number

        handler = self.handlers.get(event_data.type.value)
        if handler:
            handler(cuuid, event_data)
        else:
            logger.warning(f"Unhandled event type: {event_data.type.value}")


class ClientRegistry:
    """
    Manages client connection state, character data, and timeout handling.
    """

    def __init__(self, timeout: int) -> None:
        self.registry: dict[str, dict[str, Any]] = {}
        self.timeout = timeout

    def set_client_data(self, cuuid: str, key: str, value: Any) -> None:
        if cuuid in self.registry:
            self.registry[cuuid][key] = value

    def register_client(
        self,
        cuuid: str,
        map_name: Optional[str] = None,
        char_dict: Optional[CharData] = None,
    ) -> None:
        default_char = CharData(
            tile_pos=(0, 0), name="", facing=Direction.down, running=False
        )

        self.registry[cuuid] = {
            "map_name": map_name or "",
            "char_dict": char_dict or default_char,
            "ping_timestamp": datetime.now(),
            "event_list": {},
        }

    def update_char_field(self, cuuid: str, key: str, value: Any) -> None:
        if cuuid in self.registry and "char_dict" in self.registry[cuuid]:
            self.registry[cuuid]["char_dict"][key] = value

    def update_char_dict(
        self, cuuid: str, char_data: Optional[CharData]
    ) -> None:
        if char_data is None:
            logger.warning(f"No character data provided for CUUID: {cuuid}")
            return

        existing = self.registry[cuuid].get("char_dict")
        char_data_dict = asdict(char_data)

        if isinstance(existing, dict):
            existing.update(char_data_dict)
        elif isinstance(existing, CharData):
            updated = replace(existing, **char_data_dict)
            self.registry[cuuid]["char_dict"] = updated
        else:
            self.registry[cuuid]["char_dict"] = char_data

    def remove_client(self, cuuid: str) -> None:
        if cuuid in self.registry:
            del self.registry[cuuid]

    def check_timeouts(self, now: datetime) -> list[str]:
        timed_out = []
        for cuuid, data in self.registry.items():
            if (now - data.get("ping_timestamp", now)).seconds > self.timeout:
                timed_out.append(cuuid)
        return timed_out


class NotificationManager:
    """
    Handles sending event notifications to clients via the WebSocket server.
    """

    def __init__(
        self,
        server: WebsocketServerWrapper,
        get_next_event_number: Callable[[], int],
        event_factory: EventFactory,
    ) -> None:
        self.server = server
        self.get_next_event_number = get_next_event_number
        self.event_factory = event_factory

    def notify_client(self, cuuid: str, event_data: EventData) -> None:
        updated_event = event_data.copy(
            cuuid=cuuid, notify_type=event_data.type.notify()
        )
        json_data = json.dumps(updated_event.to_dict())

        for client_id in self.server.registry:
            if client_id != cuuid:
                self.server.notify(client_id, json_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        notify_type = event_data.type.notify()

        event_data_1 = event_data.copy(cuuid=cuuid, notify_type=notify_type)
        json_data_1 = json.dumps(event_data_1.to_dict())

        for client_id in self.server.registry:
            if client_id == cuuid:
                continue

            self.server.notify(client_id, json_data_1)

            char = self.server.registry[client_id]
            event_data_2 = self.event_factory.create_event(
                event_type=event_data.type,
                cuuid=client_id,
                map_name=char["map_name"],
                char_dict=char["char_dict"],
                notify_type=notify_type,
            )
            json_data_2 = json.dumps(event_data_2.to_dict())
            self.server.notify(cuuid, json_data_2)

    def notify_client_interaction(
        self, cuuid: str, event_data: EventData
    ) -> None:
        if event_data is None or event_data.target is None:
            logger.warning(f"Invalid interaction event from CUUID: {cuuid}")
            return

        updated_event = event_data.copy(
            target=cuuid, notify_type=event_data.type.notify()
        )
        json_data = json.dumps(updated_event.to_dict())
        self.server.notify(event_data.target, json_data)

    def send_notification(self, target_id: str, event_data: EventData) -> None:
        json_data = json.dumps(event_data.to_dict())
        self.server.notify(target_id, json_data)


class EventFactory:
    """
    Utility class for creating standardized EventData objects.
    """

    def __init__(self, get_next_event_number: Callable[[], int]) -> None:
        self.get_next_event_number = get_next_event_number

    def create_event(
        self,
        event_type: EventType,
        cuuid: str,
        map_name: str = "",
        char_dict: Optional[Union[dict[str, Any], CharData]] = None,
        notify_type: Optional[str] = None,
        target: Optional[str] = None,
    ) -> EventData:
        return EventData(
            type=event_type,
            event_number=self.get_next_event_number(),
            cuuid=cuuid,
            map_name=map_name,
            char_dict=(
                CharData(**char_dict)
                if isinstance(char_dict, dict)
                else char_dict
            ),
            notify_type=notify_type or event_type.notify(),
            target=target,
        )
