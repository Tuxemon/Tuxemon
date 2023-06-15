# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState


class PlayerInCondition(EventCondition):
    """
    Check to see if the player is at the condition position
    on a specific set of tiles.

    Script usage:
        .. code-block::

            is player_in <value>

    Script parameters:
        value: value (eg surfable) inside the tileset.

    """

    name = "player_in"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        prop = condition.parameters[0]
        world = session.client.get_state_by_name(WorldState)

        if prop == "surfable":
            if player.tile_pos in world.surfable_map:
                return True
            else:
                return False
        else:
            raise ValueError(f"{prop} isn't valid.")
