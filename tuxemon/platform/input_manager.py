# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from pygame.surface import Surface

from tuxemon.platform.combo_detector import ComboManager
from tuxemon.platform.input_device import (
    ControllerOverlaySetup,
    CoreDevices,
    GamepadSetup,
    InputDeviceSetup,
    KeyboardSetup,
    MouseSetup,
)
from tuxemon.platform.input_history import InputHistory
from tuxemon.platform.input_visualizer import InputVisualizer
from tuxemon.platform.platform_pygame.events import (
    PygameEventQueueHandler,
)
from tuxemon.prepare import SCREEN_SIZE

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.platform.afk_manager import AFKManager
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class InputManager:
    """
    Manages the input devices for the game.
    """

    def __init__(self, config: TuxemonConfig, afk_manager: AFKManager) -> None:
        """
        Initializes the input manager with the given config.
        """
        self.afk_manager = afk_manager
        self.config = config
        self.event_queue = PygameEventQueueHandler()
        self.input_history = InputHistory(config)
        self.combo_manager = ComboManager()
        self.input_visualizer = InputVisualizer(SCREEN_SIZE)
        self.core_devices = CoreDevices()
        self.extra_devices: dict[str, Any] = {}
        self._device_setups: dict[str, InputDeviceSetup] = {
            "keyboard": KeyboardSetup(),
            "gamepad": GamepadSetup(),
            "overlay": ControllerOverlaySetup(),
            "mouse": MouseSetup(),
        }
        self.setup_inputs()

    def setup_inputs(self) -> None:
        for name, setup_strategy in self._device_setups.items():
            try:
                device = setup_strategy.setup(self.event_queue, self.config)
                if device:
                    if hasattr(self.core_devices, name):
                        setattr(self.core_devices, name, device)
                    else:
                        self.extra_devices[name] = device
            except Exception as e:
                logger.error(f"Error setting up {name}: {e}")

    def process_events(self) -> Generator[PlayerInput, None, None]:
        """Processes the input events."""
        for event in self.event_queue.process_events():
            self.afk_manager.reset()
            self.input_history.record_input(event)
            self.combo_manager.process(event)
            yield event

    def update(self, time_delta: float) -> None:
        self.input_history.update(time_delta)
        self.event_queue.update_handlers(time_delta)
        self.afk_manager.update(time_delta)

    def draw_overlay(self, screen: Surface) -> None:
        if self.core_devices.overlay:
            self.core_devices.overlay.draw(screen)

    def draw_visualizer(self, screen: Surface) -> None:
        if not self.config.controller.show_input_visualizer:
            return
        all_inputs = {}
        for handler in self.event_queue.get_input_handlers():
            for button_id, player_input in handler.buttons.items():
                all_inputs[button_id] = player_input
        self.input_visualizer.draw(screen, all_inputs)

    def draw_inputs(self, screen: Surface) -> None:
        self.draw_overlay(screen)
        self.draw_visualizer(screen)
