# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections import deque
from typing import Optional

from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import translate_input_event


class InputHistory:
    def __init__(self, max_size: int = 25):
        self.raw_history: deque[PlayerInput] = deque(maxlen=max_size * 10)
        self.history: deque[PlayerInput] = deque(maxlen=max_size)
        self.last_history_event: Optional[PlayerInput] = None

    def add(self, event: PlayerInput) -> None:
        """
        Adds a new input event to the history and raw_history.
        The history stores only distinct button presses (no consecutive
        duplicates). The raw_history stores all events.

        Parameters:
            event: The input event to add to the history.
        """
        event = translate_input_event(event)

        if (
            not self.history or event.button != self.last_history_event.button
            if self.last_history_event
            else True
        ):
            self.history.append(event)
            self.last_history_event = event

        self.raw_history.append(event)

    def is_button_combo(self, buttons: list[int]) -> bool:
        """
        Checks if a specific button combination is present at the end of
        the history. This method does not modify the history.

        Parameters:
            buttons: The button combination to check for.

        Returns:
            True if the button combination is found, False otherwise.
        """
        if len(buttons) > len(self.history):
            return False

        # Check if the last len(buttons) items in history match the combo
        return all(
            self.history[-(i + 1)].button == buttons[-(i + 1)]
            for i in range(len(buttons))
        )

    def is_button_held(self, button: int, min_hold_time: int = 1) -> bool:
        """
        Checks if a specific button is being held down for a minimum amount
        of time.
        Parameters:
            button: The button to check for.
            min_hold_time: The minimum time the button must be held down for.
            return False

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
        for event in reversed(self.raw_history):
            if event.pressed:
                return event.button
        return None

    def clear_history(self) -> None:
        """Clears the history."""
        self.history.clear()

    def clear_raw_history(self) -> None:
        """Clears the raw_history."""
        self.raw_history.clear()
