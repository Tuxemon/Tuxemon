# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import PlagueType
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class NpcPlagueAttributeAction(
    EventAction,
):
    """
    Set the NPC as infected, inoculated or healthy.

    Script usage:
        .. code-block::

            npc_plague <value>[,npc_slug]

    Script parameters:
        condition: Infected, inoculated or healthy
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "npc_plague"
    value: str
    npc_slug: Union[str, None] = None

    def start(self) -> None:
        if self.npc_slug is None:
            trainer_slug = "player"
        else:
            trainer_slug = self.npc_slug
        npc = get_npc(self.session, trainer_slug)
        assert npc
        if self.value == PlagueType.infected:
            npc.plague = PlagueType.infected
        elif self.value == PlagueType.healthy:
            npc.plague = PlagueType.healthy
        elif self.value == PlagueType.inoculated:
            npc.plague = PlagueType.inoculated
        else:
            raise ValueError(
                f"{self.value} must be infected, inoculated or healthy."
            )
