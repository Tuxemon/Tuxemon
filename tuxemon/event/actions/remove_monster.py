# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class RemoveMonsterAction(EventAction):
    """
    Remove a monster from the given trainer's party if the monster is there.

    Monster is determined by instance_id, which must be passed in a game
    variable.

    Script usage:
        .. code-block::

            remove_monster <instance_id>[,npc_slug]

    Script parameters:
        instance_id: Id of the monster.
        npc_slug: Slug of the trainer. If no trainer slug is passed
            it defaults to the current player.

    """

    name = "remove_monster"
    instance_id: str
    npc_slug: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        iid = player.game_variables[self.instance_id]
        instance_id = uuid.UUID(iid)

        self.npc_slug = "player" if self.npc_slug is None else self.npc_slug
        trainer = get_npc(self.session, self.npc_slug)
        assert trainer

        monster = trainer.find_monster_by_id(instance_id)
        if monster is not None:
            player.remove_monster(monster)
