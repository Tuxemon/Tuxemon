# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random as rd
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon import formula, monster
from tuxemon.db import SeenStatus, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC


@final
@dataclass
class RandomMonsterAction(EventAction):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            random_monster <monster_level>[,trainer_slug][,exp_mod][,money_mod]

    Script parameters:
        monster_level: Level of the added monster.
        trainer_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.
        exp_mod: Experience modifier
        money_mod: Money modifier

    """

    name = "random_monster"
    monster_level: int
    trainer_slug: Union[str, None] = None
    exp: Union[int, None] = None
    money: Union[int, None] = None

    def start(self) -> None:
        trainer: Optional[NPC]
        if self.trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        # list is required as choice expects a sequence
        filters = []
        monsters = list(db.database["monster"])
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0:
                filters.append(results.slug)

        monster_slug = rd.choice(filters)

        current_monster = monster.Monster()
        current_monster.load_from_db(monster_slug)
        current_monster.set_level(self.monster_level)
        current_monster.set_moves(self.monster_level)
        current_monster.set_capture(formula.today_ordinal())
        current_monster.current_hp = current_monster.hp
        if self.exp is not None:
            current_monster.experience_modifier = self.exp
        if self.money is not None:
            current_monster.money_modifier = self.money

        trainer.add_monster(current_monster)
        trainer.tuxepedia[monster_slug] = SeenStatus.caught
