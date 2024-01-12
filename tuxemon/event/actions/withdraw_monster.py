# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction

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

            withdraw_monster <monster_id>[,npc_slug]

    Script parameters:
        monster_id: The id of the monster to pull (variable).
        npc_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.

    """

    name = "withdraw_monster"
    monster_id: str
    npc_slug: Optional[str] = None

    def start(self) -> None:
        self.npc_slug = "player" if self.npc_slug is None else self.npc_slug
        trainer = get_npc(self.session, self.npc_slug)
        assert trainer

        instance_id = uuid.UUID(trainer.game_variables[self.monster_id])
        mon = trainer.find_monster_in_storage(instance_id)
        assert mon

        trainer.remove_monster_from_storage(mon)
        trainer.add_monster(mon, len(trainer.monsters))
