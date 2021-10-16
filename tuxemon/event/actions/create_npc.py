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
import logging

import tuxemon.npc
from tuxemon import ai
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final, Union
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


class CreateNpcActionParameters(NamedTuple):
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int
    animations: Union[str, None]
    behavior: Union[str, None]


@final
class CreateNpcAction(EventAction[CreateNpcActionParameters]):
    """
    Create an NPC object and adds it to the game's current list of NPC's.

    Script usage:
        .. code-block::

            create_npc <npc_slug>,<tile_pos_x>,<tile_pos_y>[,<animations>][,<behavior>]

    Script parameters:
        npc_slug: NPC slug to look up in the NPC database.
        tile_pos_x: X position to place the NPC on.
        tile_pos_y: Y position to place the NPC on.
        animations: Sprite of the NPC. Deprecated in favor of the JSON.
        behavior: Behavior of the NPC (e.g. "wander"). Unused for now.

    """

    name = "create_npc"
    param_class = CreateNpcActionParameters

    def start(self) -> None:
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name(WorldState)
        if not world:
            return

        # Get the npc's parameters from the action
        slug = self.parameters.npc_slug

        # Ensure that the NPC doesn't already exist on the map.
        if slug in world.npcs:
            return

        # Get the npc's parameters from the action
        pos_x = self.parameters.tile_pos_x
        pos_y = self.parameters.tile_pos_y
        behavior = self.parameters.behavior

        sprite = self.parameters.animations
        if sprite:
            logger.warning(
                "%s: setting npc sprites within a map is deprecated, and may be removed in the future. "
                "Sprites should be defined in JSON before loading.",
                slug,
            )
        else:
            sprite = db.database["npc"][slug].get("sprite_name")

        # Create a new NPC object
        npc = tuxemon.npc.NPC(slug, sprite_name=sprite)
        npc.set_position((pos_x, pos_y))

        # Set the NPC object's variables
        npc.behavior = behavior
        npc.ai = ai.RandomAI()
        npc.load_party()

        # Add the NPC to the game's NPC list
        world.add_entity(npc)
