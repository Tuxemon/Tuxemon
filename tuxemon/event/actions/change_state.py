# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class ChangeStateAction(EventAction):
    """
    Change to the specified state.

    Script usage:
        .. code-block::

            change_state <state_name>

    Script parameters:
        state_name: The state name to switch to (e.g. PCState).

    """

    name = "change_state"
    state_name: str

    def start(self) -> None:
        # Don't override previous state if we are still in the state.
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError
        if current_state.name != self.state_name:
            self.session.client.push_state(self.state_name)
