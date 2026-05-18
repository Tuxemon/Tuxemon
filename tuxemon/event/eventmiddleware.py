# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tuxemon.db import Direction
from tuxemon.platform.const import events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import keymap, unicode_map
from tuxemon.prepare import DEV_TOOLS

if TYPE_CHECKING:
    from tuxemon.camera.camera import CameraManager
    from tuxemon.entity.npc import NPC
    from tuxemon.event.eventmanager import EventManager
    from tuxemon.map.manager import MapManager
    from tuxemon.movement import MovementManager
    from tuxemon.platform.input_manager import InputManager
    from tuxemon.state.manager import StateManager
    from tuxemon.world.manager import WorldMenuManager

logger = logging.getLogger(__name__)


class EventMiddleware(ABC):
    """Base class for event processing middleware."""

    @abstractmethod
    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        """
        Called before state propagation.

        Returns:
            The event, a modified event, or None to consume/stop propagation.
        """

    @abstractmethod
    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        """
        Called after state propagation.

        Returns:
            The final processed event, or None.
        """


class InputTranslatorMiddleware(EventMiddleware):
    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        new_button_id = event.button

        if event.button in keymap:
            new_button_id = keymap[event.button]

        elif event.button == events.UNICODE and event.value in unicode_map:
            new_button_id = unicode_map[event.value]

        return PlayerInput(
            button=new_button_id,
            value=event.value,
            hold_time=event.hold_time,
            previous_value=event.previous_value,
            timestamp=event.timestamp,
            hold_duration=event.hold_duration,
        )

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event


class ButtonFilterMiddleware(EventMiddleware):
    """
    Filters events based on a set of raw hardware button IDs.

    Purpose: Blocks input from specific physical keys/buttons before
    they are translated into game intentions.
    """

    def __init__(self, initially_blocked_buttons: set[int] | None = None):
        self._blocked_buttons: set[int] = (
            initially_blocked_buttons if initially_blocked_buttons else set()
        )

    def block_button(self, button_id: int) -> None:
        """Adds a raw button ID to the filter list."""
        self._blocked_buttons.add(button_id)
        logger.debug(f"Button filter blocking ID: {button_id}")

    def unblock_button(self, button_id: int) -> None:
        """Removes a raw button ID from the filter list."""
        self._blocked_buttons.discard(button_id)
        logger.debug(f"Button filter unblocking ID: {button_id}")

    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        raw_button_id = event.button

        if raw_button_id in self._blocked_buttons:
            logger.debug(
                f"Consumed event: Raw button ID {raw_button_id} is blocked by ButtonFilter."
            )
            return None

        return event

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event


class IntentionFilterMiddleware(EventMiddleware):
    """
    Filters events based on a list of currently allowed/disallowed intentions.

    Purpose: Acts as a context-dependent gate to lock/allow specific game actions
    based on the current state (e.g., in a menu or cutscene).
    """

    OPEN_GATE = "OPEN_GATE"

    def __init__(self) -> None:
        self.allowed_actions: set[Any] = set()

    def update_allowed_actions(self, actions_to_allow: set[int] | str) -> None:
        """
        Configures the gate: either a set of allowed intention IDs, or the
        string 'OPEN_GATE' to allow everything.
        """
        if (
            isinstance(actions_to_allow, str)
            and actions_to_allow == self.OPEN_GATE
        ):
            self.allowed_actions = {self.OPEN_GATE}
            logger.info("Intention Gate set to ALLOW ALL.")
        else:
            self.allowed_actions = set(actions_to_allow)
            logger.info(
                f"Intention Gate updated. Allowed actions: {self.allowed_actions}"
            )

    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        if self.OPEN_GATE in self.allowed_actions:
            return event

        action_id = event.button

        if not self.allowed_actions:
            logger.debug(f"Consumed intention {action_id}: Global block.")
            return None

        if action_id not in self.allowed_actions:
            logger.debug(
                f"Consumed intention {action_id}: Not on the allowed list."
            )
            return None

        return event

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event


class MovementMiddleware(EventMiddleware):
    """
    Handles directional and run inputs, delegating to the MovementManager.
    Consumes the event if it successfully queues or initiates movement.
    """

    def __init__(
        self,
        character: NPC,
        movement_manager: MovementManager,
        camera_manager: CameraManager,
    ):
        self.character = character
        self.movement_manager = movement_manager
        self.camera_manager = camera_manager

        self.direction_map: Mapping[int, Direction] = {
            intentions.UP: Direction.UP,
            intentions.DOWN: Direction.DOWN,
            intentions.LEFT: Direction.LEFT,
            intentions.RIGHT: Direction.RIGHT,
        }

    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        btn = event.button
        direction = self.direction_map.get(btn)

        if btn == intentions.RUN:
            self.character.mover.update_movement_state(event.held)
            return event

        # Check if directional input is for camera control
        camera = self.camera_manager.get_active_camera()
        if camera and not camera.is_following():
            return event  # Pass to CameraControlMiddleware

        # Handle directional movement
        if direction:
            if event.held:
                self.movement_manager.queue_movement(
                    self.character.slug, direction
                )
                if self.movement_manager.is_movement_allowed(self.character):
                    self.movement_manager.move_char(self.character, direction)
                return None

            if (
                not event.pressed
                and self.movement_manager.has_pending_movement(self.character)
            ):
                self.movement_manager.stop_char(self.character)
                return None

        return event

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event


class WorldCommandMiddleware(EventMiddleware):
    """
    Handles menu, interaction, and developer commands within the EventMiddleware pipeline.
    """

    def __init__(
        self,
        character: NPC,
        state_manager: StateManager,
        input_manager: InputManager,
        event_manager: EventManager,
        menu_manager: WorldMenuManager,
    ):
        self.character = character
        self.state_manager = state_manager
        self.input_manager = input_manager
        self.event_manager = event_manager
        self.menu_manager = menu_manager

    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        btn = event.button

        if btn == intentions.INTERACT:
            return event

        if btn == intentions.WORLD_MENU:
            if event.pressed:
                self.event_manager.release_controls(self.input_manager)
                self.state_manager.push_state(
                    "WorldMenuState",
                    menu_manager=self.menu_manager,
                    character=self.character,
                )
                return None
            return event

        return event

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event


class CameraControlMiddleware(EventMiddleware):
    """
    Handles directional input for moving a detached camera.
    Must be placed before MovementMiddleware.
    """

    def __init__(self, camera_manager: CameraManager):
        self.camera_manager = camera_manager

    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        btn = event.button

        if btn in (
            intentions.UP,
            intentions.DOWN,
            intentions.LEFT,
            intentions.RIGHT,
        ):
            camera = self.camera_manager.get_active_camera()

            if camera and not camera.is_following():
                result = self.camera_manager.handle_input(event)

                if result is None:
                    return None

                return result

        return event

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event


class DevToolsMiddleware(EventMiddleware):
    """
    Handles developer-only commands such as noclip and map reload.
    Should be enabled only when DEV_TOOLS is True.
    """

    def __init__(
        self,
        character: NPC,
        map_manager: MapManager,
        event_manager: EventManager,
        input_manager: InputManager,
    ):
        self.character = character
        self.map_manager = map_manager
        self.event_manager = event_manager
        self.input_manager = input_manager

    def preprocess(self, event: PlayerInput) -> PlayerInput | None:
        if not DEV_TOOLS:
            return event

        btn = event.button

        if btn == intentions.NOCLIP and event.pressed:
            self.character.ignore_collisions = (
                not self.character.ignore_collisions
            )
            return None

        if btn == intentions.RELOAD_MAP and event.pressed:
            assert self.map_manager.current_map
            self.map_manager.current_map.reload_tiles()
            return None

        return event

    def postprocess(
        self, processed_event: PlayerInput | None
    ) -> PlayerInput | None:
        return processed_event
