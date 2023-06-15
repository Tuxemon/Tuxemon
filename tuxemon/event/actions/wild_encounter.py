# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon import monster
from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.npc import NPC
from tuxemon.states.combat.combat import CombatState
from tuxemon.states.transition.flash import FlashTransition
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class WildEncounterAction(EventAction):
    """
    Start a encounter with a single wild monster.

    Script usage:
        .. code-block::

            wild_encounter <monster_slug>,<monster_level>[,exp_mod][,mon_mod][,env]

    Script parameters:
        monster_slug: Monster slug, if missing, then random.
        monster_level: Level of the added monster.
        exp_mod: Experience modifier
        mon_mod: Money modifier
        env: Environment (grass default)

    """

    name = "wild_encounter"
    monster_slug: str
    monster_level: int
    exp: Union[int, None] = None
    money: Union[int, None] = None
    env: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            return

        logger.info("Starting wild encounter!")

        current_monster = monster.Monster()
        current_monster.load_from_db(self.monster_slug)
        current_monster.level = self.monster_level
        current_monster.set_level(self.monster_level)
        current_monster.set_moves(self.monster_level)
        current_monster.current_hp = current_monster.hp
        if self.exp is not None:
            current_monster.experience_modifier = self.exp
        if self.money is not None:
            current_monster.money_modifier = self.money

        # Create an NPC object which will be this monster's "trainer"
        self.world = self.session.client.get_state_by_name(WorldState)
        npc = NPC("random_encounter_dummy", world=self.world)
        npc.add_monster(current_monster, len(npc.monsters))
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed
        current_monster.owner = None
        npc.party_limit = 0

        # Lookup the environment
        environment: str
        if self.env is None:
            environment = "grass"
        else:
            environment = self.env

        env = db.lookup(environment, table="environment")

        self.session.client.queue_state(
            "CombatState",
            players=(player, npc),
            combat_type="monster",
            graphics=env.battle_graphics,
        )

        # stop the player
        self.world.lock_controls()
        self.world.stop_player()

        # flash the screen
        self.session.client.push_state(FlashTransition())

        # Start some music!
        filename = env.battle_music
        self.session.client.event_engine.execute_action(
            "play_music",
            [filename],
        )

    def update(self) -> None:
        # If state is not queued, AND state is not active, then stop.
        try:
            self.session.client.get_queued_state_by_name("CombatState")
        except ValueError:
            try:
                self.session.client.get_state_by_name(CombatState)
            except ValueError:
                self.stop()

    def cleanup(self) -> None:
        npc = None
        if self.world:
            self.world.remove_entity("random_encounter_dummy")
