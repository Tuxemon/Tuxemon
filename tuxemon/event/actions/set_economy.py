# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.economy import Economy


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
    economy_slug: Union[str, None] = None

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        if self.economy_slug is None:
            npc.economy = Economy("default")

            return

        npc.economy = Economy(self.economy_slug)
