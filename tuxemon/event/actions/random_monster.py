# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random as rd
from dataclasses import dataclass
from typing import Union, final

from tuxemon.db import EvolutionStage, MonsterShape, db
from tuxemon.event.eventaction import EventAction


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
        # check if shape is valid
        if self.shape:
            shapes = list(MonsterShape)
            if self.shape not in shapes:
                raise ValueError(f"{self.shape} isn't valid.")
        # check if evolution stage is valid
        if self.evo:
            evos = list(EvolutionStage)
            if self.evo not in evos:
                raise ValueError(f"{self.evo} isn't valid.")

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
                raise ValueError(f"There are no monsters shape: {self.shape}")
            if self.evo and not self.shape:
                raise ValueError(f"There are no monsters stage: {self.evo}")
            if self.evo and self.shape:
                raise ValueError(
                    f"There are no monsters {self.evo} ({self.shape}).\n"
                    "Open an issue on Github, this will help us to create\n"
                    "new monsters with above-mentioned characteristics."
                )

        monster_slug = rd.choice(filters)

        self.session.client.event_engine.execute_action(
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
