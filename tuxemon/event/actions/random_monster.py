# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import EvolutionStage, MonsterModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)

lookup_cache: dict[str, MonsterModel] = {}


@final
@dataclass
class RandomMonsterAction(EventAction):
    """
    Adds a random monster to the specified trainer's party, if there is room.

    Script usage:
        .. code-block::

            random_monster <level>[,npc_slug][,exp][,mon][,shape][,evo]

    Script parameters:
        level: The level of the added monster.
        npc_slug: The slug of the trainer to receive the monster
            Defaults to the current player.
        exp: A modifier for the monster's experience.
        mon: A modifier for the monster's money yield.
        shape: The monster's shape (e.g., 'varmint', 'brute').
        evo: The monster's evolution stage (e.g., 'basic', 'stage1').
    """

    name = "random_monster"
    monster_level: int
    trainer_slug: Optional[str] = None
    exp: Optional[float] = None
    money: Optional[float] = None
    shape: Optional[str] = None
    evo: Optional[str] = None

    def start(self, session: Session) -> None:
        if not lookup_cache:
            _lookup_monsters()

        try:
            evo_stage = EvolutionStage(self.evo) if self.evo else None
        except ValueError:
            logger.error(f"'{self.evo}' is not a valid evolution stage.")
            return

        filters = [
            monster.slug
            for monster in lookup_cache.values()
            if monster.txmn_id > 0
            and monster.randomly
            and (not self.shape or monster.shape == self.shape)
            and (not self.evo or monster.stage == evo_stage)
        ]

        if not filters:
            logger.error(
                f"No valid monsters found for the given criteria "
                f"(shape: {self.shape}, evo: {self.evo})."
            )
            return

        monster_slug = random.choice(filters)

        session.client.event_engine.execute_action(
            "add_monster",
            [
                monster_slug,
                self.monster_level,
                self.trainer_slug,
                self.exp,
                self.money,
            ],
            True,
        )


def _lookup_monsters() -> None:
    global lookup_cache
    lookup_cache = {
        mon_name: result
        for mon_name in db.database["monster"]
        if (result := MonsterModel.lookup(mon_name, db)).txmn_id > 0
    }
