# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tuxemon.event import get_event_bus
from tuxemon.platform.events import PlayerInput

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class InputRecorder:
    """Manages multiple recordings and playback of PlayerInput events."""

    def __init__(self) -> None:
        self._event_bus = get_event_bus()
        self._recorded_events: list[PlayerInput] = []
        self._is_recording: bool = False
        self._is_playing_back: bool = False
        self._playback_index: int = 0
        self._current_playback_data: list[PlayerInput] | None = None
        self._recordings: dict[str, list[PlayerInput]] = {}
        self._recording_states: dict[str, dict[str, Any]] = {}
        self._initial_state: dict[str, Any] | None = None

    def start_playback(self, events: list[PlayerInput]) -> None:
        if self._is_recording:
            logger.warning("Cannot start playback while recording is active.")
            return
        self._current_playback_data = events
        self._playback_index = 0
        self._is_playing_back = True
        logger.info(f"Input playback started with {len(events)} events.")

    def start_playback_named(self, name: str) -> None:
        """Start playback from a named recording in memory."""
        if name not in self._recordings:
            logger.error(f"No recording found with name '{name}'")
            return
        self.start_playback(self._recordings[name])

    def stop_playback(self) -> None:
        """Stop playback and reset internal state."""
        self._is_playing_back = False
        self._current_playback_data = None
        self._playback_index = 0
        logger.info("Input playback stopped.")

    def start_recording(self, session: Session) -> None:
        if self._is_playing_back:
            logger.warning("Cannot start recording while playback is active.")
            return
        self._recorded_events.clear()
        self._is_recording = True

        player = session.player
        self._initial_state = {
            "map": session.client.get_map_name(),
            "player_x": player.tile_pos[0],
            "player_y": player.tile_pos[1],
            "direction": player.facing,
        }
        logger.info("Input recording started with initial state captured.")

    def record_event(self, event: PlayerInput) -> None:
        if self._is_recording:
            self._recorded_events.append(event.clone())

    def stop_recording(self, name: str | None = None) -> list[PlayerInput]:
        if not self._is_recording:
            return []
        self._is_recording = False
        logger.info("Input recording stopped.")
        if name:
            self._recordings[name] = list(self._recorded_events)
            if self._initial_state:
                self._recording_states[name] = self._initial_state
            logger.info(f"Recording saved in memory under name '{name}'")
        return self._recorded_events

    def save_to_file(self, path: Path, name: str | None = None) -> bool:
        """Save either the last recording or a named one to file."""
        events = self._recordings.get(name) if name else self._recorded_events
        state = (
            self._recording_states.get(name) if name else self._initial_state
        )
        if not events:
            logger.warning("Attempted to save, but no events were recorded.")
            return False
        try:
            data = {
                "initial_state": state or {},
                "events": [e.to_dict() for e in events],
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=4), encoding="utf-8")
            logger.info(f"Saved {len(events)} events to {path.resolve()}")
            return True
        except Exception as e:
            logger.error(f"Could not save input file {path}: {e}")
            return False

    def load_from_file(
        self, path: Path, name: str | None = None
    ) -> list[PlayerInput] | None:
        """Load events from file and optionally store under a name."""
        if not path.exists():
            logger.error(f"Input file not found: {path}")
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            events = [PlayerInput(**d) for d in data.get("events", [])]
            if name:
                self._recordings[name] = events
                self._recording_states[name] = data.get("initial_state", {})
            return events
        except Exception as e:
            logger.error(f"Could not load input file {path}: {e}")
            return None

    def next_playback_event(self) -> PlayerInput | None:
        """Return the next playback event if available."""
        if self._is_playing_back and self._current_playback_data:
            if self._playback_index < len(self._current_playback_data):
                event = self._current_playback_data[self._playback_index]
                self._playback_index += 1
                return event
            else:
                self.stop_playback()
        return None

    def list_recordings(self) -> list[str]:
        """Return all named recordings currently stored in memory."""
        return list(self._recordings.keys())

    def get_recording(self, name: str) -> list[PlayerInput] | None:
        return self._recordings.get(name)

    def get_recording_state(self, name: str) -> dict[str, Any] | None:
        """Return the initial state metadata for a named recording."""
        return self._recording_states.get(name)
