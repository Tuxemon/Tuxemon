# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import load_and_scale
from tuxemon.session import Session


@final
@dataclass
class SetBubbleAction(EventAction):
    """
    Put a bubble above player sprite.

    Script usage:
        .. code-block::

            set_bubble <npc_slug>[,bubble]

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        bubble: dots, drop, exclamation, heart, note, question, sleep,
            angry, confused, fireworks

    Example usage:
        "set_bubble spyder_shopassistant" (remove bubble from NPC)
        "set_bubble spyder_shopassistant,note" (set bubble for NPC)
        "set_bubble player,note" (set bubble for player)
        "set_bubble player" (remove bubble from player)
    """

    name = "set_bubble"
    npc_slug: str
    bubble: str | None = None

    def start(self, session: Session) -> None:
        client = session.client
        npc = session.client.get_npc(self.npc_slug)

        if npc is None:
            raise ValueError(f"NPC '{self.npc_slug}' not found.")

        filename = f"gfx/bubbles/{self.bubble}.png"

        if self.bubble is None:
            if client.map_renderer.bubble_manager.has_bubble(npc):
                client.map_renderer.bubble_manager.remove_bubble(npc)
        else:
            try:
                surface = load_and_scale(filename)
            except FileNotFoundError:
                raise ValueError(f"Bubble image '{filename}' not found.")
            else:
                client.map_renderer.bubble_manager.add_bubble(npc, surface)
