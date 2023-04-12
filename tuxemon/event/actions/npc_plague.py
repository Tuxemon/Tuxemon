# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.db import PlagueType
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class NpcPlagueAttributeAction(
    EventAction,
):
    """
    Set the NPC as infected, inoculated or sickless.

    Script usage:
        .. code-block::

            npc_plague <npc_slug>,<value>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        condition: Infected, inoculated or sickless

    """

    name = "npc_plague"
    npc_slug: str
    value: str

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        if self.value == PlagueType.infected:
            npc.plague = PlagueType.infected
        elif self.value == PlagueType.sickless:
            npc.plague = PlagueType.sickless
        elif self.value == PlagueType.inoculated:
            npc.plague = PlagueType.inoculated
        else:
            raise ValueError(f"{self.value} must be infected, inoculated or sickless.")
