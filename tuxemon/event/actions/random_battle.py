# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon import formula, prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.states.combat.combat import CombatState
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


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
        if self.nr_txmns > prepare.PARTY_LIMIT:
            logger.error(
                f"{self.nr_txmns} must be between 1 and {prepare.PARTY_LIMIT}"
            )
            return
        if self.max_level > prepare.MAX_LEVEL:
            logger.error(
                f"{self.max_level} must be between 1 and {prepare.MAX_LEVEL}"
            )
            return

        # random npc
        npcs = list(db.database["npc"])
        filters = []
        for mov in npcs:
            results = db.lookup(mov, table="npc")
            if not results.monsters:
                filters.append(results.slug)

        opponent = random.choice(filters)
        world = self.session.client.get_state_by_name(WorldState)
        npc = NPC(opponent, world=world)

        # random monster
        mons = list(db.database["monster"])
        filtered = []
        for mon in mons:
            elements = db.lookup(mon, table="monster")
            if elements.txmn_id > 0 and elements.randomly:
                filtered.append(elements.slug)

        output = random.sample(filtered, self.nr_txmns)
        for monster in output:
            level = random.randint(self.min_level, self.max_level)
            current_monster = Monster()
            current_monster.load_from_db(monster)
            current_monster.set_level(level)
            current_monster.set_moves(level)
            current_monster.set_capture(formula.today_ordinal())
            current_monster.current_hp = current_monster.hp
            current_monster.money_modifier = level
            current_monster.experience_modifier = level
            npc.add_monster(current_monster, len(npc.monsters))

        player = self.session.player

        # Lookup the environment
        env_slug = player.game_variables.get("environment", "grass")
        env = db.lookup(env_slug, table="environment")

        if not check_battle_legal(player) or not check_battle_legal(npc):
            logger.warning("battle is not legal, won't start")
            return

        # Add our players and setup combat
        logger.info(f"Starting battle with '{npc.name}'!")
        self.session.client.push_state(
            CombatState(
                players=(player, npc),
                combat_type="trainer",
                graphics=env.battle_graphics,
            )
        )

        # Start some music!
        filename = env.battle_music
        self.session.client.event_engine.execute_action(
            "play_music",
            [filename],
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(CombatState)
        except ValueError:
            self.stop()
