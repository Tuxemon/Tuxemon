# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class UnlockControlsAction(EventAction):
    """
    Unlock player controls

    Script usage:
        .. code-block::

            unlock_controls

    """

    name = "unlock_controls"

    def start(self) -> None:
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError
        if current_state.name == "SinkState":
            self.session.client.pop_state()
        else:
            raise ValueError("It has never been locked or already unlocked!")
