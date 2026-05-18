# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from tuxemon.platform.joystick_detector import JoystickDetector
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
    keyboard: PygameKeyboardInput | None = None
    gamepad: PygameGamepadInput | None = None
    overlay: PygameTouchOverlayInput | None = None
    mouse: PygameMouseInput | None = None


class InputDeviceSetup(Protocol):
    """
    Protocol for classes responsible for setting up a specific input device.
    """

    def setup(
        self,
        event_queue: PygameEventQueueHandler,
        config: TuxemonConfig,
        resolution: tuple[int, int],
    ) -> Any | None:
        """
        Configures and adds the input device to the event queue, returns the
        instance.
        """
        ...


class KeyboardSetup:
    def setup(
        self,
        event_queue: PygameEventQueueHandler,
        config: TuxemonConfig,
        resolution: tuple[int, int],
    ) -> PygameKeyboardInput | None:
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
        self,
        event_queue: PygameEventQueueHandler,
        config: TuxemonConfig,
        resolution: tuple[int, int],
    ) -> PygameGamepadInput | None:

        detector = JoystickDetector()
        joysticks = detector.detect()

        if not joysticks:
            logger.info("No usable joysticks found")
            return None

        controller_type = config.controller.type

        if controller_type is None:
            return None

        strategy = self._get_mapping_strategy(controller_type)

        gamepad = PygameGamepadInput(strategy, joysticks)
        event_queue.set_input(0, 20, gamepad)

        logger.info(
            f"{controller_type.capitalize()} gamepad set up successfully"
        )
        return gamepad


class ControllerOverlaySetup:
    def setup(
        self,
        event_queue: PygameEventQueueHandler,
        config: TuxemonConfig,
        resolution: tuple[int, int],
    ) -> PygameTouchOverlayInput | None:
        if config.controller.overlay:
            overlay = PygameTouchOverlayInput(
                config.controller.transparency, resolution
            )
            overlay.load()
            event_queue.set_input(0, 30, overlay)
            logger.info("Controller overlay set up successfully")
            return overlay
        return None


class MouseSetup:
    def setup(
        self,
        event_queue: PygameEventQueueHandler,
        config: TuxemonConfig,
        resolution: tuple[int, int],
    ) -> PygameMouseInput | None:
        if not config.controller.hide_mouse:
            mouse = PygameMouseInput()
            event_queue.set_input(0, 40, mouse)
            logger.info("Mouse set up successfully")
            return mouse
        return None
