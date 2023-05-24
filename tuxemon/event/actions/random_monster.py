# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random as rd
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon import formula, monster
from tuxemon.db import EvolutionStage, MonsterShape, SeenStatus, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


@final
@dataclass
class RandomMonsterAction(EventAction):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            random_monster <level>[,npc_slug][,exp][,mon][,shape][,evo]

    Script parameters:
        level: Level of the added monster.
        npc_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.
        exp: Experience modifier
        mon: Money modifier
        shape: Shape (eg. varmint, brute, etc.)
        evo: Stage (eg. basic, stage1, etc.)

    """

    name = "random_monster"
    monster_level: int
    trainer_slug: Union[str, None] = None
    exp: Union[int, None] = None
    money: Union[int, None] = None
    shape: Union[str, None] = None
    evo: Union[str, None] = None

    def start(self) -> None:
        trainer: Optional[NPC]
        if self.trainer_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        # check if shape is valid
        if self.shape:
            shapes = list(MonsterShape)
            if self.shape not in shapes:
                logger.error(f"{self.shape} isn't valid.")
                raise ValueError()
        # check if evolution stage is valid
        if self.evo:
            evos = list(EvolutionStage)
            if self.evo not in evos:
                logger.error(f"{self.evo} isn't valid.")
                raise ValueError()

        # list is required as choice expects a sequence
        filters = []
        monsters = list(db.database["monster"])
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0 and results.randomly:
                if not self.shape and not self.evo:
                    filters.append(results.slug)
                if self.shape and not self.evo:
                    if results.shape == self.shape:
                        filters.append(results.slug)
                if self.evo and not self.shape:
                    if results.stage == self.evo:
                        filters.append(results.slug)
                if self.evo and self.shape:
                    if (
                        results.stage == self.evo
                        and results.shape == self.shape
                    ):
                        filters.append(results.slug)

        if not filters:
            if self.shape and not self.evo:
                logger.error(f"There are no monsters shape: {self.shape}")
                raise ValueError()
            if self.evo and not self.shape:
                logger.error(f"There are no monsters stage: {self.evo}")
                raise ValueError()
            if self.evo and self.shape:
                logger.error(
                    f"There are no monsters {self.evo} ({self.shape}).\n"
                    "Open an issue on Github, this will help us to create\n"
                    "new monsters with above-mentioned characteristics."
                )
                raise ValueError()

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

        trainer.add_monster(current_monster, len(trainer.monsters))
        trainer.tuxepedia[monster_slug] = SeenStatus.caught
