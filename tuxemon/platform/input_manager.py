# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, Optional

from pygame.surface import Surface

from tuxemon.platform.combo_detector import ComboManager
from tuxemon.platform.input_history import InputHistory
from tuxemon.platform.input_visualizer import InputVisualizer
from tuxemon.platform.platform_pygame.events import (
    InputMappingStrategy,
    PlayStationMapping,
    PygameEventQueueHandler,
    PygameGamepadInput,
    PygameKeyboardInput,
    PygameMouseInput,
    PygameTouchOverlayInput,
    XboxMapping,
)
from tuxemon.prepare import SCREEN_SIZE

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class InputManager:
    """
    Manages the input devices for the game.
    """

    def __init__(self, config: TuxemonConfig) -> None:
        """
        Initializes the input manager with the given config.
        """
        self.event_queue = PygameEventQueueHandler()
        self.input_history = InputHistory()
        self.controller = config.controller
        self.input = config.input
        self.controller_overlay: Optional[PygameTouchOverlayInput] = None
        self.setup_inputs()
        self.combo_manager = ComboManager()
        self.input_visualizer = InputVisualizer(SCREEN_SIZE)
        self.show_visualizer = self.controller.show_input_visualizer

    def setup_inputs(self) -> None:
        """
        Sets up the input devices based on the config.
        """
        setup_methods = [
            self.setup_keyboard,
            self.setup_gamepad,
            self.setup_controller_overlay,
            self.setup_mouse,
        ]

        for setup_method in setup_methods:
            try:
                setup_method()
            except Exception as e:
                logger.error(f"Error setting up {setup_method.__name__}: {e}")

    def setup_keyboard(self) -> None:
        """
        Sets up the keyboard input device.
        """
        if self.input.keyboard_button_map:
            keyboard = PygameKeyboardInput(self.input.keyboard_button_map)
            self.event_queue.add_input(0, keyboard)
            logger.info("Keyboard set up successfully")

    def setup_gamepad(self) -> None:
        """
        Sets up the gamepad input device.
        """
        if self.controller.type:
            strategy = self._get_mapping_strategy(self.controller.type)
            gamepad = PygameGamepadInput(strategy)
            self.event_queue.add_input(0, gamepad)
            logger.info(
                f"{self.controller.type.capitalize()} gamepad set up successfully"
            )

    def _get_mapping_strategy(
        self, controller_type: str
    ) -> InputMappingStrategy:
        if controller_type == "xbox":
            return XboxMapping()
        elif controller_type == "ps4":
            return PlayStationMapping()
        else:
            raise ValueError(f"Unsupported controller type: {controller_type}")

    def setup_controller_overlay(self) -> None:
        """
        Sets up the controller overlay input device.
        """
        if self.controller.overlay:
            self.controller_overlay = PygameTouchOverlayInput(
                self.controller.transparency
            )
            self.controller_overlay.load()
            self.event_queue.add_input(0, self.controller_overlay)
            logger.info("Controller overlay set up successfully")

    def setup_mouse(self) -> None:
        """
        Sets up the mouse input device.
        """
        if not self.controller.hide_mouse:
            self.event_queue.add_input(0, PygameMouseInput())
            logger.info("Mouse set up successfully")

    def process_events(self) -> Generator[PlayerInput, None, None]:
        """Processes the input events."""
        for event in self.event_queue.process_events():
            self.input_history.add(event)
            self.combo_manager.process(event)
            yield event

    def draw_visualizer(self, screen: Surface) -> None:
        all_inputs = {}
        for player_handlers in self.event_queue._inputs.values():
            for handler in player_handlers:
                for button_id, player_input in handler.buttons.items():
                    all_inputs[button_id] = player_input
        self.input_visualizer.draw(screen, all_inputs)
