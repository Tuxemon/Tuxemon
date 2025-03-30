# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import translate_input_event


class InputHistory:
    def __init__(self, max_size: int = 25):
        self.max_size = max_size
        self.history: Deque[PlayerInput] = deque()
        self.raw_max_size = max_size * 10
        self.raw_history: Deque[PlayerInput] = deque()

    def add(self, event: PlayerInput) -> None:
        """
        Adds a new input event to the history and raw_history.
        The history stores only distinct button presses (no consecutive
        duplicates). The raw_history stores all events.

        Parameters:
            event: The input event to add to the history.
        """
        event = translate_input_event(event)

        if not self.history or event.button != self.history[-1].button:
            self.history.append(event)
            if len(self.history) > self.max_size:
                self.history.popleft()

        self.raw_history.append(event)
        if len(self.raw_history) > self.raw_max_size:
            self.raw_history.popleft()

    def is_button_combo(self, buttons: list[int]) -> bool:
        """
        Checks if a specific button combination is present in the history.

        Parameters:
            buttons: The button combination to check for.

        Returns:
            True if the button combination is found, False otherwise.
        """
        if len(buttons) > self.max_size:
            raise ValueError(
                "Button combination is longer than max history size."
            )

        history_iter = iter(self.history)
        matched_buttons = 0

        for event in history_iter:
            if event.button == buttons[matched_buttons]:
                matched_buttons += 1
                if matched_buttons == len(buttons):
                    for _ in range(len(buttons)):
                        self.history.popleft()
                    return True
        return False

    def is_button_held_down(self, button: int, min_hold_time: int) -> bool:
        """
        Checks if a specific button is being held down for a minimum amount
        of time.

        Parameters:
            button: The button to check for.
            min_hold_time: The minimum time the button must be held down for.

        Returns:
            True if the button is being held down for the minimum time,
                False otherwise.
        """
        for event in reversed(self.raw_history):
            if event.button == button:
                return event.is_held(min_hold_time)
        return False

    def count_button_clicks(self) -> dict[int, int]:
        """
        Counts the number of times each button has been clicked
        (pressed and released). Counts clicks based on the raw_history.
        """
        click_counts: dict[int, int] = {}
        for event in self.raw_history:
            if event.pressed or event.released:
                click_counts[event.button] = (
                    click_counts.get(event.button, 0) + 1
                )
        return click_counts

    def get_last_button_clicked(self) -> Optional[int]:
        """
        Gets the last button clicked from the history.

        Returns:
            The last button clicked, or None if the history is empty.
        """
        if self.raw_history and self.raw_history[-1].pressed:
            return self.raw_history[-1].button
        return None

    def clear_history(self) -> None:
        """Clears the history."""
        self.history.clear()

    def clear_raw_history(self) -> None:
        """Clears the raw_history."""
        self.raw_history.clear()
