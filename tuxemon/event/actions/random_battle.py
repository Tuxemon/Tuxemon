# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon import formula
from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event.actions.play_music import PlayMusicAction
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
        player = self.session.player

        if self.nr_txmns < 1 or self.nr_txmns > 6:
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
        for ele in output:
            level = random.randint(self.min_level, self.max_level)
            current_monster = Monster()
            current_monster.load_from_db(ele)
            current_monster.set_level(level)
            current_monster.set_moves(level)
            current_monster.set_capture(formula.today_ordinal())
            current_monster.current_hp = current_monster.hp
            current_monster.money_modifier = level
            current_monster.experience_modifier = level
            npc.add_monster(current_monster, len(npc.monsters))

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            logger.warning("battle is not legal, won't start")
            return

        # Lookup the environment
        env_slug = player.game_variables.get("environment", "grass")
        env = db.lookup(env_slug, table="environment")

        # Add our players and setup combat
        logger.info("Starting battle with '{self.npc_slug}'!")
        self.session.client.push_state(
            CombatState(
                players=(player, npc),
                combat_type="trainer",
                graphics=env.battle_graphics,
            )
        )

        # Start some music!
        filename = env.battle_music
        PlayMusicAction(filename=filename).start()

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(CombatState)
        except ValueError:
            self.stop()
