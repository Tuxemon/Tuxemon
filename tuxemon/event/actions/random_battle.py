# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon import formula, prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import MonsterModel, NpcModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.states.combat.combat import CombatState
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)

lookup_cache_mon: dict[str, MonsterModel] = {}
lookup_cache_npc: dict[str, NpcModel] = {}


@final
@dataclass
class RandomBattleAction(EventAction):
    """
    Start random battle with a random npc with a determined
    number of monster in a certain range of levels.

    Script usage:
        .. code-block::

            random_battle nr_txmns,min_level,max_level

    Script parameters:
        nr_txmns: Number of tuxemon (1 to 6).
        min_level: Minimum level of the party.
        max_level: Maximum level of the party.

    """

    name = "random_battle"
    nr_txmns: int
    min_level: int
    max_level: int

    def start(self) -> None:
        if not lookup_cache_npc or not lookup_cache_mon:
            _lookup()

        # Validate party size and max level
        if not (1 <= self.nr_txmns <= prepare.PARTY_LIMIT):
            logger.error(
                f"Party size {self.nr_txmns} must be between 1 and {prepare.PARTY_LIMIT}"
            )
            return
        if not (1 <= self.max_level <= prepare.MAX_LEVEL):
            logger.error(
                f"Max level {self.max_level} must be between 1 and {prepare.MAX_LEVEL}"
            )
            return

        npc_filters = list(lookup_cache_npc.values())
        opponent = random.choice(npc_filters)
        world = self.session.client.get_state_by_name(WorldState)
        npc = NPC(opponent.slug, world=world)

        monster_filters = list(lookup_cache_mon.values())
        monsters = random.sample(monster_filters, self.nr_txmns)
        for monster in monsters:
            level = random.randint(self.min_level, self.max_level)
            current_monster = Monster()
            current_monster.load_from_db(monster.slug)
            current_monster.set_level(level)
            current_monster.set_moves(level)
            current_monster.set_capture(formula.today_ordinal())
            current_monster.current_hp = current_monster.hp
            current_monster.money_modifier = level
            current_monster.experience_modifier = level
            npc.add_monster(current_monster, len(npc.monsters))

        player = self.session.player
        env_slug = player.game_variables.get("environment", "grass")
        env = db.lookup(env_slug, table="environment")

        if not (check_battle_legal(player) and check_battle_legal(npc)):
            logger.warning("Battle is not legal, won't start")
            return

        logger.info(f"Starting battle with '{npc.name}'!")
        self.session.client.push_state(
            CombatState(
                players=(player, npc),
                combat_type="trainer",
                graphics=env.battle_graphics,
            )
        )

        self.session.client.current_music.play(env.battle_music)

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(CombatState)
        except ValueError:
            self.stop()


def _lookup() -> None:
    monsters = list(db.database["monster"])
    npcs = list(db.database["npc"])

    for mon in monsters:
        _mon = db.lookup(mon, table="monster")
        if _mon.txmn_id > 0 and _mon.randomly:
            lookup_cache_mon[mon] = _mon

    for npc in npcs:
        _npc = db.lookup(npc, table="npc")
        if not _npc.monsters:
            lookup_cache_npc[npc] = _npc
