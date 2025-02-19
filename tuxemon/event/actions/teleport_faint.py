# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class TeleportFaintAction(EventAction):
    """
    Teleport the player to the point in the teleport_faint variable.

    Usually used to teleport to the last visited Tuxcenter, as when
    all monsters in the party faint.

    Script usage:
        .. code-block::

            teleport_faint [trans_time]

    Script parameters:
        trans_time: Transition time in seconds - default 0.3

    """

    name = "teleport_faint"
    trans_time: Optional[float] = None

    def start(self) -> None:
        player = self.session.player
        client = self.session.client
        current_state = client.current_state
        if current_state and current_state.name == "DialogState":
            client.pop_state()

        if "teleport_faint" in player.game_variables:
            teleport = str(player.game_variables["teleport_faint"]).split(" ")
        else:
            logger.error("The teleport_faint variable has not been set.")
            return

        if self.trans_time is not None:
            teleport.append(str(self.trans_time))
        action = client.event_engine
        action.execute_action("transition_teleport", teleport)
