# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.platform.afk_manager import AFKManager
    from tuxemon.platform.events import PlayerInput
    from tuxemon.platform.input_recorder import InputRecorder

logger = logging.getLogger(__name__)


class InputManager:
    """
    Manages the input devices for the game.
    """

    def __init__(
        self,
        config: TuxemonConfig,
        afk_manager: AFKManager,
        recorder: InputRecorder,
        resolution: tuple[int, int],
    ) -> None:
        """
        Initializes the input manager with the given config.
        """
        self.afk_manager = afk_manager
        self.config = config
        self.recorder = recorder
        self.resolution = resolution
        self.event_queue = PygameEventQueueHandler()
        self.input_history = InputHistory(config)
        self.combo_manager = ComboManager()
        self.input_visualizer = InputVisualizer(self.resolution)
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
                device = setup_strategy.setup(
                    self.event_queue, self.config, self.resolution
                )
                if device:
                    if hasattr(self.core_devices, name):
                        setattr(self.core_devices, name, device)
                    else:
                        self.extra_devices[name] = device
            except Exception as e:
                logger.error(f"Error setting up {name}: {e}")

    def process_events(self) -> Generator[PlayerInput, None, None]:
        """Processes the input events."""
        # Playback mode
        if self.recorder._is_playing_back:
            self.event_queue.set_event_filter(lambda e: False)
            # Only yield playback events
            event = self.recorder.next_playback_event()
            if event:
                yield event
            return

        # Live input mode
        if self.event_queue.filter_active:
            self.event_queue.clear_event_filter()

        for event in self.event_queue.process_events():
            self.afk_manager.reset()
            self.input_history.record_input(event)
            self.combo_manager.process(event)

            if self.recorder._is_recording:
                self.recorder.record_event(event)

            yield event

    def update(self, dt: float) -> None:
        self.input_history.update(dt)
        self.event_queue.update_handlers(dt)
        self.afk_manager.update(dt)

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
