# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

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
    npc_slug: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player
        if self.npc_slug is None:
            trainer_slug = "player"
        else:
            trainer_slug = self.npc_slug
        trainer = get_npc(self.session, trainer_slug)
        assert trainer
        for mon in trainer.monsters:
            index = trainer.monsters.index(mon)
            player.game_variables[f"iid_slot_{index}"] = str(
                mon.instance_id.hex
            )
