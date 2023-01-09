# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class NpcRun(EventAction):
    """
    Set the NPC movement speed to the global run speed.

    Script usage:
        .. code-block::

            npc_run <npc_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "npc_run"
    npc_slug: str

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        npc.moverate = self.session.client.config.player_runrate
