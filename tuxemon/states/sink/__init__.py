from __future__ import annotations

from tuxemon.state import State
from tuxemon.platform.events import PlayerInput
from typing import Optional


class SinkState(State):
    """State blocking input to lower states in the stack."""

    transparent = True

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
