# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, Optional

from tuxemon.platform.platform_pygame.events import (
    PygameEventQueueHandler,
    PygameGamepadInput,
    PygameKeyboardInput,
    PygameMouseInput,
    PygameTouchOverlayInput,
)

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
        self.config = config
        self.controller_overlay: Optional[PygameTouchOverlayInput] = None
        self.setup_inputs()

    def setup_inputs(self) -> None:
        """
        Sets up the input devices based on the config.
        """
        try:
            self.setup_keyboard()
            self.setup_gamepad()
            self.setup_controller_overlay()
            self.setup_mouse()
        except Exception as e:
            logger.error(f"Unexpected error setting up inputs: {e}")
            raise

    def setup_keyboard(self) -> None:
        """
        Sets up the keyboard input device.
        """
        if self.config.keyboard_button_map:
            keyboard = PygameKeyboardInput(self.config.keyboard_button_map)
            self.event_queue.add_input(0, keyboard)
            logger.info("Keyboard set up successfully")

    def setup_gamepad(self) -> None:
        """
        Sets up the gamepad input device.
        """
        if self.config.gamepad_button_map:
            gamepad = PygameGamepadInput(
                self.config.gamepad_button_map, self.config.gamepad_deadzone
            )
            self.event_queue.add_input(0, gamepad)
            logger.info("Gamepad set up successfully")

    def setup_controller_overlay(self) -> None:
        """
        Sets up the controller overlay input device.
        """
        if self.config.controller_overlay:
            self.controller_overlay = PygameTouchOverlayInput(
                self.config.controller_transparency
            )
            self.controller_overlay.load()
            self.event_queue.add_input(0, self.controller_overlay)
            logger.info("Controller overlay set up successfully")

    def setup_mouse(self) -> None:
        """
        Sets up the mouse input device.
        """
        if not self.config.hide_mouse:
            self.event_queue.add_input(0, PygameMouseInput())
            logger.info("Mouse set up successfully")

    def process_events(self) -> Generator[PlayerInput, None, None]:
        """
        Processes the input events.
        """
        return self.event_queue.process_events()
