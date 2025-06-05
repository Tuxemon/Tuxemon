# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

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

            teleport_faint <character>[,trans_time][,rgb]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        trans_time: Transition time in seconds - default 0.3
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(0,0,0)

    eg: "teleport_faint player,3"
    eg: "teleport_faint player,3,255:0:0:50" (red)
    """

    name = "teleport_faint"
    character: str
    trans_time: Optional[float] = None
    rgb: Optional[str] = None

    def start(self, session: Session) -> None:
        character = get_npc(session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return

        client = session.client
        current_state = client.current_state
        if current_state and current_state.name == "DialogState":
            client.remove_state_by_name("DialogState")

        if character.teleport_faint.is_default():
            logger.error(
                "The teleport_faint variable has not been set, use 'set_teleport_faint'."
            )
            return
        else:
            teleport = character.teleport_faint

        action = client.event_engine
        action.execute_action(
            "transition_teleport",
            [
                teleport.map_name,
                teleport.x,
                teleport.y,
                self.trans_time,
                self.rgb,
            ],
        )
