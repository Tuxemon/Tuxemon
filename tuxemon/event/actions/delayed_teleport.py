# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class DelayedTeleportAction(EventAction):
    """
    Set teleport information.

    Teleport will be triggered during screen transition.

    Only use this if followed by a transition.

    Script usage:
        .. code-block::

            delayed_teleport <map_name>,<position_x>,<position_y>

    Script parameters:
        map_name: Name of the map to teleport to.
        position_x: X position to teleport to.
        position_y: Y position to teleport to.

    """

    name = "delayed_teleport"
    map_name: str
    position_x: int
    position_y: int

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)

        if world.delayed_teleport:
            logger.error("Stop, there is a teleport in progress")
            return
        player = self.session.player
        player.remove_collision(player.tile_pos)
        world.delayed_teleport = True
        world.delayed_mapname = self.map_name
        world.delayed_x = self.position_x
        world.delayed_y = self.position_y
