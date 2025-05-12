# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RemoveStateAction(EventAction):
    """
    Remove the specified state or the last active one.

    This action allows the removal of a specific state from the client's
    active state list. If no state name is provided, it removes the current
    state, except for certain protected states (e.g., "WorldState" and
    "BackgroundState").

    Script usage:
        .. code-block::

            remove_state [state_name]

    Script parameters:
        state_name: The name of the state to remove (e.g., "PCState").
            If not provided, the last active state will be removed, unless it's a
            protected state.
    """

    name = "remove_state"
    state_name: Optional[str] = None

    def start(self, session: Session) -> None:
        client = session.client
        state_name = self.state_name

        if client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if state_name is None:
            if client.current_state.name not in [
                "WorldState",
                "BackgroundState",
            ]:
                logger.info(f"{client.current_state.name} is removed.")
                client.pop_state()
        else:
            if state_name not in client.active_state_names:
                logger.error(f"{state_name} isn't active.")
                return
            client.remove_state_by_name(state_name)
            logger.info(f"{state_name} is removed.")
