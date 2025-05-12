# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


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

    def start(self, session: Session) -> None:
        session.client.npc_manager.remove_npc(self.npc_slug)
