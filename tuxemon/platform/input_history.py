# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, NamedTuple

from tuxemon.event.eventmiddleware import InputTranslatorMiddleware

if TYPE_CHECKING:
    from tuxemon.config import TuxemonConfig
    from tuxemon.platform.events import PlayerInput


class ComboHint(NamedTuple):
    match_length: int = 0
    total_combo_length: int = 0


class HistoryEntry(NamedTuple):
    event: PlayerInput
    age: float


class InputHistory:
    def __init__(self, config: TuxemonConfig, max_size: int = 25):
        self.history: deque[HistoryEntry] = deque(maxlen=max_size)
        self.last_history_event: PlayerInput | None = None
        self.held_timers: dict[int, float] = {}
        self._click_counts: dict[int, int] = {}
        self._buttons_down: set[int] = set()
        self._last_button_clicked: int | None = None
        self._current_combo_hint: ComboHint = ComboHint()
        self.combo_window_seconds = config.controller.combo_window_seconds
        self.translator = InputTranslatorMiddleware()

    @property
    def current_combo_hint(self) -> ComboHint:
        return self._current_combo_hint

    def record_input(self, event: PlayerInput) -> None:
        """
        Adds a new input event to the history.
        The history stores only distinct button presses (no consecutive
        duplicates), *unless* repeated presses represent separate taps.
        """
        translated_event = self.translator.preprocess(event)
        if translated_event is None:
            return

        button = translated_event.button

        if translated_event.pressed:
            self.held_timers[button] = 0.0
        elif translated_event.released:
            self.held_timers.pop(button, None)

        if translated_event.released and button in self._buttons_down:
            self._click_counts[button] = self._click_counts.get(button, 0) + 1
            self._buttons_down.discard(button)

        if translated_event.pressed:
            self._buttons_down.add(button)
            self._last_button_clicked = button

            if (
                self.last_history_event
                and self.last_history_event.button == button
                and self.last_history_event.pressed
            ):
                return

            self.history.append(HistoryEntry(translated_event, 0.0))
            self.last_history_event = translated_event

    def update(self, dt: float) -> None:
        self.update_history(dt, max_age_s=self.combo_window_seconds)

        for button in list(self.held_timers.keys()):
            self.held_timers[button] += dt

    def update_history(
        self, dt: float, max_age_s: float | None = None
    ) -> None:
        """
        Removes inputs from the history if they are older than max_age_s.
        This enforces a 'combo window'.
        """
        max_age_s = max_age_s or self.combo_window_seconds

        # Age all events
        self.history = deque(
            (HistoryEntry(e.event, e.age + dt) for e in self.history),
            maxlen=self.history.maxlen,
        )

        # Remove expired events
        while self.history and self.history[0].age > max_age_s:
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
        history_buttons = [e.event.button for e in self.history]
        history_len = len(history_buttons)

        if combo_len <= history_len:
            if history_buttons[-combo_len:] == buttons:
                self._current_combo_hint = ComboHint(combo_len, combo_len)
                return True

        max_len = min(combo_len, history_len)

        match_count = 0
        for length in range(max_len, 0, -1):
            if history_buttons[:length] == buttons[:length]:
                match_count = length
                break

        if match_count == 0:
            for length in range(max_len, 0, -1):
                if history_buttons[-length:] == buttons[:length]:
                    match_count = length
                    break

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

    def get_last_button_clicked(self) -> int | None:
        """Returns the ID of the last button pressed down."""
        return self._last_button_clicked

    def clear_history(self) -> None:
        """Clears the history."""
        self.history.clear()
