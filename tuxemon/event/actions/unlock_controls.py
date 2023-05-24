# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.sink import SinkState

logger = logging.getLogger(__name__)


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

    def start(self) -> None:
        sink_state = self.session.client.get_state_by_name(SinkState)

        if sink_state:
            logger.info(f"Controls unlocked")
            self.session.client.remove_state(sink_state)
