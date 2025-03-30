# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.economy import Economy
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetEconomyAction(EventAction):
    """
    Set the economy (prices of items) of the npc or player.

    Script usage:
        .. code-block::

            set_economy <npc_slug>,<economy_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        economy_slug: Slug of an economy.

    """

    name = "set_economy"
    npc_slug: str
    economy_slug: str

    def start(self) -> None:
        player = self.session.player
        npc = get_npc(self.session, self.npc_slug)
        assert npc

        npc.economy = Economy(self.economy_slug)
        items = npc.economy.load_economy_items(player)
        npc.economy.add_economy_to_npc(npc, items)
