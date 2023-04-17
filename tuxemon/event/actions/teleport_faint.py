# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

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

            teleport_faint

    """

    name = "teleport_faint"

    def start(self) -> None:
        player = self.session.player

        # If game variable exists, then teleport:
        if "teleport_faint" in player.game_variables:
            teleport = player.game_variables["teleport_faint"].split(" ")
        else:
            logger.error(
                f"Teleport_faint action failed, because the teleport_faint variable has not been set."
            )
            return

        # Start the screen transition
        # self.game.event_engine.execute_action("screen_transition", [.3])

        # Call the teleport action
        self.session.client.event_engine.execute_action("teleport", teleport)
