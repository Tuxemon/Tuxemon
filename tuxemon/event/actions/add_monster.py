# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.database.runtime import db
from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.session import Session


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
    npc_slug: str | None = None
    exp: float | None = None
    money: float | None = None

    def start(self, session: Session) -> None:
        player = session.player
        self.npc_slug = self.npc_slug or "player"
        trainer = session.client.get_npc(self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        if self.monster_slug not in db.database["monster"]:
            if player.game_variables.has(self.monster_slug):
                monster_slug = player.game_variables.get(self.monster_slug)
            else:
                raise ValueError(
                    f"{self.monster_slug} doesn't exist (monster or variable)"
                )
        else:
            monster_slug = self.monster_slug

        monster = Monster.spawn_base(monster_slug, self.monster_level)

        if self.exp is not None:
            monster.set_experience_modifier(self.exp)
        if self.money is not None:
            monster.money_modifier = self.money

        trainer.party.add_monster(monster, len(trainer.monsters))
        trainer.tuxepedia.register_caught(monster.slug)
        player.game_variables.set(self.name, monster.instance_id.hex)
