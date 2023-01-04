# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

import tuxemon.npc
from tuxemon import ai
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CreateNpcAction(EventAction):
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
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int
    animations: Union[str, None] = None
    behavior: Union[str, None] = None

    def start(self) -> None:
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name(WorldState)

        # Get the npc's parameters from the action
        slug = self.npc_slug

        # Ensure that the NPC doesn't already exist on the map.
        if slug in world.npcs:
            return

        sprite = self.animations
        if sprite:
            logger.warning(
                "%s: setting npc sprites within a map is deprecated, and may be removed in the future. "
                "Sprites should be defined in JSON before loading.",
                slug,
            )
        else:
            sprite = db.lookup(slug, "npc").sprite_name

        # Create a new NPC object
        npc = tuxemon.npc.NPC(slug, sprite_name=sprite, world=world)
        npc.set_position((self.tile_pos_x, self.tile_pos_y))

        # Set the NPC object's variables
        npc.behavior = self.behavior
        npc.ai = ai.RandomAI()
        npc.load_party()
