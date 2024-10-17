# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CreateNpcAction(EventAction):
    """
    Create an NPC object and adds it to the game's current list of NPC's.

    Script usage:
        .. code-block::

            create_npc <npc_slug>,<tile_pos_x>,<tile_pos_y>[,<behavior>]

    Script parameters:
        npc_slug: NPC slug to look up in the NPC database.
        tile_pos_x: X position to place the NPC on.
        tile_pos_y: Y position to place the NPC on.
        behavior: Behavior of the NPC (e.g. "wander"). Unused for now.

    """

    name = "create_npc"
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int
    behavior: Optional[str] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)

        slug = self.npc_slug

        for element in world.npcs:
            if element.slug == slug:
                logger.error(
                    f"'{slug}' already exists on the map. Skipping creation."
                )
                return

        npc = NPC(slug, world=world)
        client = self.session.client.event_engine
        client.execute_action(
            "char_position", [slug, self.tile_pos_x, self.tile_pos_y], True
        )

        npc.behavior = self.behavior
        npc.load_party()
