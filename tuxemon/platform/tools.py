# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING

from tuxemon.platform.const import buttons, intentions

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus
    from tuxemon.platform.events import PlayerInput

keymap = {
    buttons.UP: intentions.UP,
    buttons.DOWN: intentions.DOWN,
    buttons.LEFT: intentions.LEFT,
    buttons.RIGHT: intentions.RIGHT,
    buttons.A: intentions.INTERACT,
    buttons.B: intentions.RUN,
    buttons.START: intentions.WORLD_MENU,
    buttons.BACK: intentions.WORLD_MENU,
}

unicode_map = {
    "n": intentions.NOCLIP,
    "r": intentions.RELOAD_MAP,
}


class ButtonEdgeFilter:
    def __init__(self) -> None:
        self.previous_states: dict[int, bool] = {}

    def is_new_press(self, button: int, is_pressed: bool) -> bool:
        """
        Checks if a press event is the leading edge (i.e., the button just
        became pressed this frame).
        """
        was_pressed = self.previous_states.get(button, False)
        self.previous_states[button] = is_pressed
        return is_pressed and not was_pressed

    def is_new_release(self, button: int, is_pressed: bool) -> bool:
        """
        Checks if a release event is the trailing edge (i.e., the button just
        became released this frame).
        """
        was_pressed = self.previous_states.get(button, False)
        self.previous_states[button] = is_pressed
        return not is_pressed and was_pressed


class ScriptInputCache:
    def __init__(self, event_bus: EventBus):
        self._pressed_buttons: set[int] = set()
        self._released_buttons: set[int] = set()
        self._held_buttons: set[int] = set()
        event_bus.subscribe("PLAYER_INPUT", self.handle_input_event)

    def handle_input_event(self, event: PlayerInput) -> None:
        """Called by the EventBus when a state-approved input occurs."""
        if event.pressed:
            self._pressed_buttons.add(event.button)
            self._held_buttons.add(event.button)
        else:
            self._released_buttons.add(event.button)
            self._held_buttons.discard(event.button)

    def clear_frame_state(self) -> None:
        """Called once per frame (e.g., at the start of Client.update())."""
        self._pressed_buttons.clear()
        self._released_buttons.clear()

    def was_button_pressed(self, button_id: int) -> bool:
        return button_id in self._pressed_buttons

    def was_button_released(self, button_id: int) -> bool:
        return button_id in self._released_buttons

    def is_button_held(self, button_id: int) -> bool:
        return button_id in self._held_buttons
