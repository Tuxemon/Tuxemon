# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class GetPartyMonsterAction(EventAction):
    """
    Saves all the iids (party) in variables.

    Script usage:
        .. code-block::

            get_party_monster [npc_slug]

    Script parameters:
        npc_slug: npc slug name (e.g. "npc_maple") - default "player"
    """

    name = "get_party_monster"
    npc_slug: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        self.npc_slug = self.npc_slug or "player"
        trainer = session.client.get_npc(self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        for index, mon in enumerate(trainer.monsters):
            player.game_variables.set(f"iid_slot_{index}", mon.instance_id.hex)
