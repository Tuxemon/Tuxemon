# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
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

            random_monster <level>[,npc_slug][,exp][,mon]

    Script parameters:
        level: The level of the added monster.
        npc_slug: The slug of the trainer to receive the monster
            Defaults to the current player.
        exp: A modifier for the monster's experience.
        mon: A modifier for the monster's money yield.

    Additional selection rules:
        - Only monsters with ``randomly = True`` are considered.
        - Monsters that would evolve at or before the given level
          (``monster.can_evolve_at_level(level)``) are excluded.
        - Monsters whose current form requires a higher level than the one
          provided (``monster.is_underleveled_for_form(level)``) are excluded.
        - Monsters with ``txmn_id <= 0`` are ignored.
    """

    name = "random_monster"
    monster_level: int
    trainer_slug: str | None = None
    exp: float | None = None
    money: float | None = None

    def start(self, session: Session) -> None:
        if not lookup_cache:
            _lookup_monsters()

        filters = [
            monster.slug
            for monster in lookup_cache.values()
            if monster.txmn_id > 0
            and monster.randomly
            and not monster.can_evolve_at_level(self.monster_level)
            and not monster.is_underleveled_for_form(self.monster_level)
        ]

        if not filters:
            logger.error("No valid monsters found for the given criteria.")
            self.stop()
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
