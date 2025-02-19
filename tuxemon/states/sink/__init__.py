# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

from tuxemon.platform.events import PlayerInput
from tuxemon.state import State


class SinkState(State):
    """State blocking input to lower states in the stack."""

    transparent = True

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        return None
