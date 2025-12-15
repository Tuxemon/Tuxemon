# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING, NamedTuple, Optional

from tuxemon.platform.tools import translate_input_event

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.platform.events import PlayerInput


class ComboHint(NamedTuple):
    match_length: int = 0
    total_combo_length: int = 0


class InputHistory:
    def __init__(self, config: TuxemonConfig, max_size: int = 25):
        self.history: deque[PlayerInput] = deque(maxlen=max_size)
        self.last_history_event: Optional[PlayerInput] = None
        self.held_timers: dict[int, float] = {}
        self._click_counts: dict[int, int] = {}
        self._buttons_down: set[int] = set()
        self._last_button_clicked: Optional[int] = None
        self._current_combo_hint: ComboHint = ComboHint()
        self.combo_window_seconds = config.controller.combo_window_seconds

    @property
    def current_combo_hint(self) -> ComboHint:
        return self._current_combo_hint

    def record_input(self, event: PlayerInput) -> None:
        """
        Adds a new input event to the history.
        The history stores only distinct button presses (no consecutive
        duplicates).
        """
        event = translate_input_event(event)

        if event.pressed:
            self.held_timers[event.button] = 0.0
        elif event.released:
            self.held_timers.pop(event.button, None)

        if event.pressed:
            self._last_button_clicked = event.button
            if event.button not in self._buttons_down:
                self._buttons_down.add(event.button)
        elif event.released and event.button in self._buttons_down:
            self._click_counts[event.button] = (
                self._click_counts.get(event.button, 0) + 1
            )
            self._buttons_down.discard(event.button)

        if (
            not self.last_history_event
            or event.button != self.last_history_event.button
        ):
            self.history.append(event)
            self.last_history_event = event

    def update(self, time_delta: float) -> None:
        self.update_history(max_age_s=self.combo_window_seconds)
        for button in list(self.held_timers.keys()):
            self.held_timers[button] += time_delta

    def update_history(self, max_age_s: Optional[float] = None) -> None:
        """
        Removes inputs from the history if they are older than max_age_s.
        This enforces a 'combo window'.
        """
        max_age_s = max_age_s or self.combo_window_seconds
        cutoff_time = time.time() - max_age_s

        while self.history and self.history[0].timestamp < cutoff_time:
            self.history.popleft()

            if not self.history:
                self.last_history_event = None

    def get_hold_time(self, button: int) -> float:
        return self.held_timers.get(button, 0.0)

    def get_button_click_count(self, button: int) -> int:
        """Returns the total click count for a specific button."""
        return self._click_counts.get(button, 0)

    def reset_click_tracking(self) -> None:
        """Clears click counts and last button clicked."""
        self._click_counts.clear()
        self._buttons_down.clear()
        self._last_button_clicked = None

    def is_button_combo(self, buttons: list[int]) -> bool:
        """
        Checks if a specific button combination is present at the end of
        the history and updates the partial match hint.
        """
        combo_len = len(buttons)
        history_len = len(self.history)
        match_count = 0

        history_list = list(self.history)

        if combo_len <= history_len:
            history_buttons_suffix = [
                e.button for e in history_list[-combo_len:]
            ]
            if history_buttons_suffix == buttons:
                self._current_combo_hint = ComboHint(combo_len, combo_len)
                return True

            for length in range(combo_len - 1, 0, -1):
                history_suffix = [e.button for e in history_list[-length:]]
                combo_prefix = buttons[:length]

                if history_suffix == combo_prefix:
                    match_count = length
                    break

        if history_len < combo_len:
            match_count = history_len

        self._current_combo_hint = ComboHint(match_count, combo_len)
        return False

    def is_button_held(self, button: int, min_hold_time: float = 1.0) -> bool:
        """
        Checks if a specific button is currently being held down for at least
        the given duration.

        Parameters:
            button: The button to check.
            min_hold_time: Minimum time (in seconds) the button must be held.

        Returns:
            True if the button is being held for at least min_hold_time,
            False otherwise.
        """
        return self.held_timers.get(button, 0.0) >= min_hold_time

    def count_button_clicks(self) -> dict[int, int]:
        """
        Returns a copy of the total click counts for all buttons.
        """
        return dict(self._click_counts)

    def get_last_button_clicked(self) -> Optional[int]:
        """Returns the ID of the last button pressed down."""
        return self._last_button_clicked

    def clear_history(self) -> None:
        """Clears the history."""
        self.history.clear()
