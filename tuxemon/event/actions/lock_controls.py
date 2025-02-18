# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.sink import SinkState


@final
@dataclass
class LockControlsAction(
    EventAction,
):
    """
    Lock player controls

    Script usage:
        .. code-block::

            lock_controls

    """

    name = "lock_controls"

    def start(self) -> None:
        self.session.client.push_state(SinkState())
