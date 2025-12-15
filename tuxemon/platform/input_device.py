# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Protocol

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

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig

logger = logging.getLogger(__name__)


@dataclass
class CoreDevices:
    keyboard: Optional[PygameKeyboardInput] = None
    gamepad: Optional[PygameGamepadInput] = None
    overlay: Optional[PygameTouchOverlayInput] = None
    mouse: Optional[PygameMouseInput] = None


class InputDeviceSetup(Protocol):
    """
    Protocol for classes responsible for setting up a specific input device.
    """

    def setup(
        self, event_queue: PygameEventQueueHandler, config: TuxemonConfig
    ) -> Optional[Any]:
        """
        Configures and adds the input device to the event queue, returns the
        instance.
        """
        ...


class KeyboardSetup:
    def setup(
        self, event_queue: PygameEventQueueHandler, config: TuxemonConfig
    ) -> Optional[PygameKeyboardInput]:
        if config.input.keyboard_button_map:
            keyboard = PygameKeyboardInput(config.input.keyboard_button_map)
            event_queue.set_input(0, 10, keyboard)
            logger.info("Keyboard set up successfully")
            return keyboard
        return None


class GamepadSetup:
    def _get_mapping_strategy(
        self, controller_type: str
    ) -> InputMappingStrategy:
        if controller_type == "xbox":
            return XboxMapping()
        elif controller_type == "ps4":
            return PlayStationMapping()
        else:
            raise ValueError(f"Unsupported controller type: {controller_type}")

    def setup(
        self, event_queue: PygameEventQueueHandler, config: TuxemonConfig
    ) -> Optional[PygameGamepadInput]:
        controller_type = config.controller.type
        if controller_type:
            strategy = self._get_mapping_strategy(controller_type)
            gamepad = PygameGamepadInput(strategy)
            event_queue.set_input(0, 20, gamepad)
            logger.info(
                f"{controller_type.capitalize()} gamepad set up successfully"
            )
            return gamepad
        return None


class ControllerOverlaySetup:
    def setup(
        self, event_queue: PygameEventQueueHandler, config: TuxemonConfig
    ) -> Optional[PygameTouchOverlayInput]:
        if config.controller.overlay:
            overlay = PygameTouchOverlayInput(config.controller.transparency)
            overlay.load()
            event_queue.set_input(0, 30, overlay)
            logger.info("Controller overlay set up successfully")
            return overlay
        return None


class MouseSetup:
    def setup(
        self, event_queue: PygameEventQueueHandler, config: TuxemonConfig
    ) -> Optional[PygameMouseInput]:
        if not config.controller.hide_mouse:
            mouse = PygameMouseInput()
            event_queue.set_input(0, 40, mouse)
            logger.info("Mouse set up successfully")
            return mouse
        return None
