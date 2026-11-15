# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class ParkExperienceAction(EventAction):
    """
    Shows the results of the Park session.

    Script usage:
        .. code-block::

            park_experience

    Script parameters:
        option: Either 'start' or 'stop'
    """

    name = "park_experience"
    option: str

    def start(self, session: Session) -> None:
        if self.option == "start":
            session.client.park_session.activate_session()
        elif self.option == "stop":
            session.client.park_session.deactivate_session()
            self._handle_stop(session)
        else:
            raise ValueError(f"{self.option} must be 'start' or 'stop'")

    def _handle_stop(self, session: Session) -> None:
        self.client = session.client
        session.player.game_variables.remove("park_out")

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        self.client.push_state("ParkState", session=session)

    def update(self, session: Session, dt: float) -> None:
        if self.option == "stop":
            if "ParkState" not in session.client.active_state_names:
                self.stop()
        else:
            self.stop()
