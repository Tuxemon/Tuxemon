# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from tuxemon.network.networking import (
    EventData,
    EventType,
    populate_client,
    update_client,
)
from tuxemon.states import world_state as world

if TYPE_CHECKING:
    from tuxemon.network.client import TuxemonClient


logger = logging.getLogger(__name__)


EventHandler = Callable[["EventDispatcher", EventData], None]


class EventDispatcher:
    handlers: dict[EventType, EventHandler] = {}

    @classmethod
    def handler(
        cls, event_type: EventType
    ) -> Callable[[EventHandler], EventHandler]:
        def wrapper(func: EventHandler) -> EventHandler:
            cls.handlers[event_type] = func
            return func

        return wrapper

    def __init__(self, client: TuxemonClient) -> None:
        self.client = client
        self.game = client.game

    def dispatch(self, event_dict: dict[str, Any]) -> None:
        """
        Parse an incoming event dict and dispatch it to the appropriate handler.
        """
        try:
            event_data = EventData.from_dict(event_dict)
        except Exception as e:
            logger.warning(f"Failed to parse event: {e}")
            return

        handler = self.handlers.get(event_data.type)
        if handler is None:
            logger.warning(f"No handler for event type {event_data.type}")
            return

        handler(self, event_data)


@EventDispatcher.handler(EventType.CLIENT_DISCONNECTED)
def handle_client_disconnected(
    self: EventDispatcher, event_data: EventData
) -> None:
    cuuid = event_data.cuuid
    if cuuid is None:
        logger.warning("Missing cuuid in CLIENT_DISCONNECTED event")
        return

    self.client.registry.pop(cuuid, None)
    logger.info(f"Client {cuuid} disconnected.")


@EventDispatcher.handler(EventType.PUSH_SELF)
def handle_push_self(self: EventDispatcher, event_data: EventData) -> None:
    cuuid = event_data.cuuid
    if cuuid is None:
        logger.warning("Missing cuuid in PUSH_SELF event")
        return

    self.client.registry.setdefault(cuuid, {})
    sprite = populate_client(
        cuuid, event_data, self.game, self.client.registry
    )
    update_client(sprite, event_data.char_dict, self.game)

    logger.info(f"Processed PUSH_SELF event for client {cuuid}.")


@EventDispatcher.handler(EventType.CLIENT_MOVE_START)
def handle_client_move_start(
    self: EventDispatcher, event_data: EventData
) -> None:
    cuuid = event_data.cuuid
    direction = event_data.direction
    if cuuid is None or direction is None:
        logger.warning("Missing data in CLIENT_MOVE_START event")
        return

    sprite = self.client.registry.get(cuuid, {}).get("sprite")
    if sprite:
        sprite.facing = direction
        for d in sprite.direction:
            sprite.direction[d] = d == direction

    logger.info(f"Client {cuuid} started moving {direction}.")


@EventDispatcher.handler(EventType.CLIENT_MOVE_COMPLETE)
def handle_client_move_complete(
    self: EventDispatcher, event_data: EventData
) -> None:
    cuuid = event_data.cuuid
    if cuuid is None or event_data.char_dict is None:
        logger.warning("Missing data in CLIENT_MOVE_COMPLETE event")
        return

    sprite = self.client.registry.get(cuuid, {}).get("sprite")
    if sprite:
        sprite._last_tile_pos = event_data.char_dict.tile_pos
        for d in sprite.direction:
            sprite.direction[d] = False

    logger.info(f"Client {cuuid} completed their move.")


@EventDispatcher.handler(EventType.CLIENT_KEYDOWN)
def handle_keydown(self: EventDispatcher, event_data: EventData) -> None:
    cuuid = event_data.cuuid
    kb_key = event_data.kb_key
    if cuuid is None or kb_key is None:
        logger.warning("Missing data in CLIENT_KEYDOWN event")
        return

    sprite = self.client.registry.get(cuuid, {}).get("sprite")
    if sprite and kb_key == "SHIFT":
        sprite.running = True

    logger.info(f"Client {cuuid} pressed {kb_key}.")


@EventDispatcher.handler(EventType.CLIENT_KEYUP)
def handle_keyup(self: EventDispatcher, event_data: EventData) -> None:
    cuuid = event_data.cuuid
    kb_key = event_data.kb_key
    if cuuid is None or kb_key is None:
        logger.warning("Missing data in CLIENT_KEYUP event")
        return

    sprite = self.client.registry.get(cuuid, {}).get("sprite")
    if sprite and kb_key == "SHIFT":
        sprite.running = False

    logger.info(f"Client {cuuid} released {kb_key}.")


@EventDispatcher.handler(EventType.CLIENT_FACING)
def handle_client_facing(self: EventDispatcher, event_data: EventData) -> None:
    cuuid = event_data.cuuid
    if cuuid is None or event_data.char_dict is None:
        logger.warning("Missing data in CLIENT_FACING event")
        return

    sprite = self.client.registry.get(cuuid, {}).get("sprite")
    if sprite and not sprite.moving:
        sprite.facing = event_data.char_dict.facing

    logger.info(f"Client {cuuid} updated facing direction.")


@EventDispatcher.handler(EventType.CLIENT_INTERACTION)
def handle_interaction(self: EventDispatcher, event_data: EventData) -> None:
    cuuid = event_data.cuuid
    if cuuid is None:
        logger.warning("Missing cuuid in CLIENT_INTERACTION event")
        return

    world_state = self.game.get_state_by_name(world.WorldState)
    world_state.handle_interaction(event_data, self.client.registry)

    logger.info(f"Processed interaction for client {cuuid}.")


@EventDispatcher.handler(EventType.CLIENT_START_BATTLE)
def handle_client_start_battle(
    self: EventDispatcher, event_data: EventData
) -> None:
    cuuid = event_data.cuuid
    if cuuid is None or event_data.char_dict is None:
        logger.warning("Missing data in CLIENT_START_BATTLE event")
        return

    sprite = self.client.registry.get(cuuid, {}).get("sprite")
    if sprite:
        sprite.running = False
        sprite._last_tile_pos = event_data.char_dict.tile_pos
        for d in sprite.direction:
            sprite.direction[d] = False

    logger.info(f"Client {cuuid} started a battle.")
