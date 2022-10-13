from __future__ import annotations

from typing import Optional

from tuxemon.platform.events import PlayerInput
from tuxemon.state import State


class SinkState(State):
    """State blocking input to lower states in the stack."""

    transparent = True

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
