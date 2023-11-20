# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import load_and_scale
from tuxemon.states.world.worldstate import WorldState


@final
@dataclass
class SetBubbleAction(EventAction):
    """
    Put a bubble above player sprite.

    Script usage:
        .. code-block::

            set_bubble [bubble][,npc_slug]

    Script parameters:
        bubble: dots, drop, exclamation, heart, note, question, sleep,
            angry, confused, fireworks
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    eg. "set_bubble ,spyder_shopassistant" (remove bubble NPC)
    eg. "set_bubble note,spyder_shopassistant" (set bubble NPC)
    eg. "set_bubble note" (set bubble player)
    eg. "set_bubble" (remove bubble player)

    """

    name = "set_bubble"
    bubble: Optional[str] = None
    npc_slug: Optional[str] = None

    def start(self) -> None:
        client = self.session.client

        self.npc_slug = "player" if self.npc_slug is None else self.npc_slug
        npc = get_npc(self.session, self.npc_slug)
        assert npc

        world = client.get_state_by_name(WorldState)
        filename = f"gfx/bubbles/{self.bubble}.png"

        if self.bubble is None:
            if npc in world.bubble:
                del world.bubble[npc]
        else:
            try:
                surface = load_and_scale(filename)
            except:
                raise ValueError(f"gfx/bubbles/{self.bubble}.png not found")
            else:
                world.bubble[npc] = surface
