# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.sink import SinkState


@final
@dataclass
class UnlockControlsAction(
    EventAction,
):
    """
    Unlock player controls

    Script usage:
        .. code-block::

            unlock_controls

    """

    name = "unlock_controls"

    def start(self, session: Session) -> None:
        sink_state = session.client.get_state_by_name(SinkState)

        if sink_state:
            session.client.remove_state(sink_state)
