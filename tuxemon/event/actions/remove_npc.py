# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class RemoveNpcAction(EventAction):
    """
    Remove an NPC object from the list of NPCs.

    Script usage:
        .. code-block::

            remove_npc <npc_slug>

    Script parameters:
        npc_slug: Npc slug name (e.g. "npc_maple").

    """

    name = "remove_npc"
    npc_slug: str

    def start(self) -> None:
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name(WorldState)

        # Get the npc's parameters from the action
        world.remove_entity(self.npc_slug)
