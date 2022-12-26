#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

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
