# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from tuxemon import prepare
from tuxemon.platform.const import intentions

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.npc import NPC
    from tuxemon.platform.events import PlayerInput
    from tuxemon.world.manager import WorldMenuManager

logger = logging.getLogger(__name__)


@dataclass
class InputHandlerConfig:
    handler: Callable[[PlayerInput], Optional[PlayerInput]]
    description: str
    dev_only: bool = False


class WorldInputHandler:
    """Handles input events specific to the WorldState."""

    def __init__(
        self,
        character: NPC,
        client: BaseClient,
        menu_manager: WorldMenuManager,
    ):
        self.character = character
        self.client = client
        self.menu_manager = menu_manager

    def handle_run(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Toggles the player's running movement state."""
        self.character.mover.update_movement_state(event.held)
        return event

    def handle_noclip(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Toggles noclip mode for the player (dev tool)."""
        if prepare.DEV_TOOLS and event.pressed:
            self.character.ignore_collisions = (
                not self.character.ignore_collisions
            )
            return None
        return event

    def handle_reload_map(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Reloads the current map tiles (dev tool)."""
        if prepare.DEV_TOOLS and event.pressed:
            assert self.client.map_manager.current_map
            self.client.map_manager.current_map.reload_tiles()
            return None
        return event

    def handle_world_menu(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Opens the world menu when triggered."""
        if event.pressed:
            logger.info("Opening main menu!")
            self.client.event_manager.release_controls(
                self.client.input_manager
            )
            self.client.push_state(
                "WorldMenuState",
                menu_manager=self.menu_manager,
                character=self.character,
            )
            return None
        return event

    def handle_interact(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Handles interaction input (placeholder for multiplayer logic)."""
        if event.pressed and self.character:
            if False:  # Multiplayer logic placeholder
                # self.check_interactable_space() would be called here
                return None
        return event

    def get_handlers(self) -> dict[int, InputHandlerConfig]:
        mapping = {
            "run": intentions.RUN,
            "noclip": intentions.NOCLIP,
            "reload_map": intentions.RELOAD_MAP,
            "world_menu": intentions.WORLD_MENU,
            "interact": intentions.INTERACT,
        }

        handlers = {}
        for name, button in mapping.items():
            method = getattr(self, f"handle_{name}", None)
            if method:
                handlers[button] = InputHandlerConfig(method, f"Handle {name}")
        return handlers


class InputRouter:
    def __init__(self) -> None:
        self.routes: dict[int, InputHandlerConfig] = {}

    def register(self, button: int, config: InputHandlerConfig) -> None:
        self.routes[button] = config

    def route(self, event: PlayerInput) -> Optional[PlayerInput]:
        config = self.routes.get(event.button)
        if config:
            return config.handler(event)
        return event
