# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class RemoveTechAction(EventAction):
    """
    Remove a specific tech from a specific monster.

    Script usage:
        .. code-block::

            remove_tech <tech_id>[,npc_slug]

    Script parameters:
        tech_id: Id of the monster (name of the variable).
        npc_slug: npc slug name (e.g. "npc_maple") - default "player"

    eg. "remove_tech name_variable"
    eg. "remove_tech name_variable,maple"

    """

    name = "remove_tech"
    tech_id: str
    npc_slug: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        if self.npc_slug is None:
            trainer_slug = "player"
        else:
            trainer_slug = self.npc_slug
        trainer = get_npc(self.session, trainer_slug)
        assert trainer

        # look for the technique
        tech_id = uuid.UUID(
            player.game_variables[self.tech_id],
        )

        for mon in trainer.monsters:
            technique = mon.find_tech_by_id(tech_id)
            if technique:
                mon.moves.remove(technique)
