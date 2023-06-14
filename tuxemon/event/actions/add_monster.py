# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon import formula
from tuxemon.db import SeenStatus, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.npc import NPC


@final
@dataclass
class AddMonsterAction(EventAction):
    """
    Add a monster to the specified trainer's party if there is room.

    Script usage:
        .. code-block::

            add_monster <mon_slug>,<mon_level>[,npc_slug][,exp_mod][,money_mod]

    Script parameters:
        mon_slug: Monster slug to look up in the monster database or name variable
            where it's stored the mon_slug
        mon_level: Level of the added monster.
        npc_slug: Slug of the trainer that will receive the monster. It
            defaults to the current player.
        exp_mod: Experience modifier
        money_mod: Money modifier

    """

    name = "add_monster"
    monster_slug: str
    monster_level: int
    trainer_slug: Union[str, None] = None
    exp: Union[int, None] = None
    money: Union[int, None] = None

    def start(self) -> None:
        player = self.session.player
        trainer: Optional[NPC]
        if self.trainer_slug is None:
            trainer = player
        else:
            trainer = get_npc(self.session, self.trainer_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            self.trainer_slug or "player"
        )

        # check monster existence
        _monster: str = ""
        verify = list(db.database["monster"])
        if self.monster_slug not in verify:
            if self.monster_slug in player.game_variables:
                _monster = player.game_variables[self.monster_slug]
            else:
                raise ValueError(
                    f"{self.monster_slug} doesn't exist (monster or variable)."
                )
        else:
            _monster = self.monster_slug

        current_monster = Monster()
        current_monster.load_from_db(_monster)
        current_monster.set_level(self.monster_level)
        current_monster.set_moves(self.monster_level)
        current_monster.set_capture(formula.today_ordinal())
        current_monster.current_hp = current_monster.hp
        if self.exp is not None:
            current_monster.experience_modifier = self.exp
        if self.money is not None:
            current_monster.money_modifier = self.money

        trainer.add_monster(current_monster, len(trainer.monsters))
        trainer.tuxepedia[current_monster.slug] = SeenStatus.caught
