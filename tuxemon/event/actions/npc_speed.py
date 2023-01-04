# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class NpcSpeed(EventAction):
    """
    Set the NPC movement speed to a custom value.

    Script usage:
        .. code-block::

            npc_speed <npc_slug> <speed>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        speed: Speed amount.

    """

    name = "npc_speed"
    npc_slug: str
    speed: float

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        npc.moverate = self.speed
        # Just set some sane limit to avoid losing sprites
        assert 0 < npc.moverate < 20
