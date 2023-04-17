# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.map import dirs2, get_direction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class PlayerFaceAction(EventAction):
    """
    Make the player face a certain direction.

    Script usage:
        .. code-block::

            player_face <direction>

    Script parameters:
        direction: Direction to face. It can be a npc slug to face or one of
            "left", "right", "up", or "down".

    """

    name = "player_face"
    direction: str  # Using Direction as the typehint breaks the Action

    def start(self) -> None:
        # Get the parameters to determine what direction the player will face.
        direction = self.direction
        if direction not in dirs2:
            target = get_npc(self.session, direction)
            assert target
            direction = get_direction(
                self.session.player.tile_pos,
                target.tile_pos,
            )

        # If we're doing a transition, only change the player's facing when
        # we've reached the apex of the transition.
        world_state = self.session.client.get_state_by_name(WorldState)

        if world_state.in_transition:
            world_state.delayed_facing = direction
        else:
            self.session.player.facing = direction
