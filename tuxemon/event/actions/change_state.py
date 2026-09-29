# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger()


@final
@dataclass
class ChangeStateAction(EventAction):
    """
    Change to the specified state (generic).

    This action handles state transitions that do not require specific
    additional parameters beyond the state name itself.

    Script usage:
        .. code-block::

            change_state <state_name>

    Script parameters:
        state_name: The state name to switch to.
    """

    name = "change_state"
    state_name: str

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name == self.state_name:
            logger.error(
                f"The state '{self.state_name}' is already active. No action taken."
            )
            self.stop()
            return

        self.client.push_state(self.state_name)

    def update(self, session: Session, dt: float) -> None:
        if self.state_name not in session.client.active_state_names:
            self.stop()
