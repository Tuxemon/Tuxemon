# -*- coding: utf-8 -*-
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

import tuxemon.core.npc
from tuxemon.core import ai
from tuxemon.core.db import db
from tuxemon.core.event.eventaction import EventAction

logger = logging.getLogger(__name__)

class CreateNpcAction(EventAction):
    """Creates an NPC object and adds it to the game's current list of NPC's.

    Valid Parameters: slug, tile_pos_x, tile_pos_y, animations, behavior
    """
    name = "create_npc"
    valid_parameters = [
        (str, "npc_slug"),
        (int, "tile_pos_x"),
        (int, "tile_pos_y"),
        (str, "animations"),
        (str, "behavior")
    ]

    def start(self):
        world = self.session.world

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
                slug
            )
        else:
            sprite = db.database['npc'][slug].get('sprite_name')

        # Create a new NPC object
        npc = tuxemon.core.npc.NPC(slug, sprite_name=sprite)
        npc.set_position((pos_x, pos_y))

        # Set the NPC object's variables
        npc.behavior = behavior
        npc.ai = ai.AI()

        # Add the NPC to the game's NPC list
        world.add_entity(npc)
