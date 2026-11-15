# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.constants.dialog_speed import resolve_character_delay
from tuxemon.ui.text import TextArea
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.event.eventbus import EventBus

logger = logging.getLogger(__name__)


@dataclass
class SplitAlertState:
    """Manages the state for an alert that is split into multiple lines."""

    dialog_lines: list[str]
    dialog_index: int = 0
    dialog_speed: str = CONFIG.dialog_speed

    def current_line(self) -> str | None:
        """Returns the current line to be displayed."""
        if 0 <= self.dialog_index < len(self.dialog_lines):
            return self.dialog_lines[self.dialog_index]
        return None

    def advance(self) -> None:
        """Move to the next line index."""
        self.dialog_index += 1


@dataclass
class AlertEntry:
    message: str
    text_area: TextArea
    callback: Callable[[], None] | None
    dialog_speed: str
    split_lines: bool
    split_state: SplitAlertState | None = None


class AlertManager:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._final_callback: Callable[[], None] | None = None
        self._time_accum: float = 0.0
        self.character_delay = resolve_character_delay(CONFIG.dialog_speed)

        self._alert_queue: deque[AlertEntry] = deque()
        self._is_busy: bool = False
        self._active_area: TextArea | None = None
        self._active_split_state: SplitAlertState | None = None

    def update(self, dt: float) -> None:
        area = self._active_area
        if area is None or not area.drawing_text:
            return

        self._time_accum += dt
        while self._time_accum >= self.character_delay and area.drawing_text:
            try:
                next(area)
            except StopIteration:
                self._on_line_complete()
                break
            self._time_accum -= self.character_delay

    def _current_text_area(self) -> TextArea | None:
        """Return the currently active TextArea being animated."""
        return self._active_area

    def animate_text(
        self, text_area: TextArea | None, text: str, dialog_speed: str
    ) -> None:
        """Animate text in the given TextArea at the specified speed."""
        if text_area is None:
            logger.error("No TextArea available to animate text.")
            return

        text_area.text = text
        self.character_delay = resolve_character_delay(dialog_speed)

        if self.character_delay == 0.0:
            try:
                for _ in text_area:
                    pass
            except Exception as e:
                logger.warning(f"Unexpected error while dumping text: {e}")

            self._on_line_complete()

    def alert(
        self,
        message: str,
        text_area: TextArea,
        callback: Callable[[], None] | None = None,
        dialog_speed: str = CONFIG.dialog_speed,
        split_lines: bool = False,
    ) -> None:
        """Queue a new alert message for display in a TextArea."""
        split_state: SplitAlertState | None = None
        if split_lines:
            lines = message.splitlines()
            if lines:
                split_state = SplitAlertState(
                    dialog_lines=lines, dialog_speed=dialog_speed
                )

        self._alert_queue.append(
            AlertEntry(
                message,
                text_area,
                callback,
                dialog_speed,
                split_lines,
                split_state,
            )
        )
        if not self._is_busy:
            self._process_next_alert()

    def _process_next_alert(self) -> None:
        """Start processing the next alert in the queue."""
        if self._alert_queue:
            self._is_busy = True
            next_alert = self._alert_queue.popleft()
            self._active_area = next_alert.text_area
            self._active_split_state = (
                next_alert.split_state
            )  # Set the active state

            def alert_complete_callback() -> None:
                try:
                    if next_alert.callback:
                        next_alert.callback()
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")

            self._final_callback = alert_complete_callback

            if next_alert.split_lines:
                # If there is no split state (empty message), finish immediately
                if not self._active_split_state:
                    self._on_alert_complete()
                    return

                first_line = self._active_split_state.current_line()
                if first_line is None:
                    # No lines to show, finish immediately
                    self._on_alert_complete()
                    return

                self.event_bus.publish(
                    "DIALOG_STARTED",
                    payload={
                        "state": "DialogState",
                        "message": first_line,
                        "split_lines": True,
                    },
                )

                self._animate_next_line(
                    self._active_split_state, next_alert.text_area
                )
                self._active_split_state.advance()
            else:
                self.event_bus.publish(
                    "DIALOG_STARTED",
                    payload={
                        "state": "DialogState",
                        "message": next_alert.message,
                        "split_lines": False,
                    },
                )
                self.animate_text(
                    next_alert.text_area,
                    next_alert.message,
                    next_alert.dialog_speed,
                )
        else:
            self._is_busy = False
            self._active_area = None
            self._active_split_state = None

    def _animate_next_line(
        self, split_state: SplitAlertState, text_area: TextArea
    ) -> None:
        """Helper to animate the current line from the split state."""
        line = split_state.current_line()
        if line is not None:
            self.animate_text(text_area, line, split_state.dialog_speed)
        else:
            self._on_alert_complete()

    def advance_dialog_line(
        self, dialog_speed: str, text_area: TextArea
    ) -> None:
        """Advance to the next line of a split-line alert."""
        if self._active_split_state:
            line = self._active_split_state.current_line()

            if line is not None:
                self.animate_text(text_area, line, dialog_speed)
                self._active_split_state.advance()
            else:
                # All lines done
                self._active_split_state = None
                self._on_alert_complete()
        else:
            # Not a split alert, or state is complete
            self._on_alert_complete()

    def _on_line_complete(self) -> None:
        """Handle completion of a line, advancing or finishing the alert."""
        # Check if we are in a multi-line alert and if there are more lines
        if self._active_split_state:
            next_line = self._active_split_state.current_line()

            if next_line is not None:
                # More lines remain — wait for DialogState to advance or
                # auto-advance if delay is 0
                logger.debug(
                    "Waiting for DialogState to advance to the next line."
                )

        # If no split state, or the split state is finished, finalize the alert.
        if (
            self._active_split_state is None
            or self._active_split_state.current_line() is None
        ):
            self._on_alert_complete()

    def _on_alert_complete(self) -> None:
        """Handle completion of an alert and invoke its callback."""
        if self._final_callback:
            try:
                self._final_callback()
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
            finally:
                self._final_callback = None

        # Always finish the alert, even if no callback
        self._finish_alert()

    def _finish_alert(self) -> None:
        """Mark the current alert as finished and process the next one."""
        self._is_busy = False
        self._active_split_state = None
        self._process_next_alert()

    def dump_remaining_text(self, text_area: TextArea) -> None:
        """Dump all remaining characters in the current line immediately."""
        if text_area is None:
            logger.error("No TextArea available to dump remaining text.")
            return

        # Dump all remaining characters in the current line
        try:
            for _ in text_area:
                pass
        except Exception as e:
            logger.warning(f"Error dumping remaining text: {e}")

        # After dumping, handle line completion (advance or close)
        self._on_line_complete()

    def is_dialog_complete(self, text_area: TextArea) -> bool:
        """Return True if the given TextArea has finished drawing text."""
        if text_area is None:
            return True
        return not text_area.drawing_text

    def is_busy(self) -> bool:
        """Return True if the manager is currently processing an alert."""
        return self._is_busy

    def current_message(self) -> str | None:
        """Return the current message line being displayed, if any."""
        if self._active_split_state:
            return self._active_split_state.current_line()
        return None
