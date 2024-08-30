# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


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
    npc_slug: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        self.npc_slug = self.npc_slug or "player"
        trainer = get_npc(self.session, self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        for index, mon in enumerate(trainer.monsters):
            player.game_variables[f"iid_slot_{index}"] = str(
                mon.instance_id.hex
            )
