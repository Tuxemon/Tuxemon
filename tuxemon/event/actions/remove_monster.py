# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Union, final

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

            remove_monster <instance_id>[,trainer_slug]

    Script parameters:
        instance_id: Id of the monster.
        trainer_slug: Slug of the trainer. If no trainer slug is passed
            it defaults to the current player.

    """

    name = "remove_monster"
    instance_id: str
    trainer_slug: Union[str, None] = None

    def start(self) -> None:
        iid = self.session.player.game_variables[self.instance_id]
        instance_id = uuid.UUID(iid)
        trainer_slug = self.trainer_slug

        trainer = (
            self.session.player
            if trainer_slug is None
            else get_npc(self.session, trainer_slug)
        )
        assert trainer

        monster = trainer.find_monster_by_id(instance_id)
        if monster is not None:
            self.session.player.remove_monster(monster)
