# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_monster_in_storage, get_npc
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

            withdraw_monster <variable>[,npc_slug]

    Script parameters:
        variable: Name of the variable where to store the monster id.
        npc_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.

    """

    name = "withdraw_monster"
    variable: str
    npc_slug: Optional[str] = None

    def start(self) -> None:
        self.npc_slug = "player" if self.npc_slug is None else self.npc_slug
        trainer = get_npc(self.session, self.npc_slug)
        if trainer is None:
            logger.error(f"{self.npc_slug} not found")
            return

        if self.variable not in trainer.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(trainer.game_variables[self.variable])
        monster = get_monster_in_storage(self.session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return
        character = monster.owner
        if character is None:
            logger.error("Monster owner not found")
            return
        character.remove_monster_from_storage(monster)
        trainer.add_monster(monster, len(trainer.monsters))
        logger.info(f"{trainer.name} withdrawn {monster.name}!")
