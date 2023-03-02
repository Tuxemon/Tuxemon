# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


@final
@dataclass
class WithdrawMonsterAction(EventAction):
    """
    Pull a monster from the given trainer's storage and puts it in their party.

    Note:
        If the trainer's party is already full then the monster will be
        deposited into the default storage box automatically.

    Script usage:
        .. code-block::

            withdraw_monster <monster_id>[,trainer_slug]

    Script parameters:
        monster_id: The id of the monster to pull (variable).
        trainer_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.

    """

    name = "withdraw_monster"
    monster_id: str
    trainer: Union[str, None] = None

    def start(self) -> None:
        trainer: Optional[NPC]
        if self.trainer is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, self.trainer)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer or "player"
        )
        instance_id = uuid.UUID(trainer.game_variables[self.monster_id])
        mon = trainer.find_monster_in_storage(instance_id)
        assert mon

        trainer.remove_monster_from_storage(mon)
        trainer.add_monster(mon)
