# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import monster, prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
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

            wild_encounter <monster_slug>,<monster_level>[,exp_mod][,mon_mod][,env][,rgb]

    Script parameters:
        monster_slug: Monster slug.
        monster_level: Level of monster.
        exp_mod: Experience modifier.
        mon_mod: Money modifier.
        env: Environment (grass default)
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(255,255,255)

    """

    name = "wild_encounter"
    monster_slug: str
    monster_level: int
    exp: Optional[int] = None
    money: Optional[int] = None
    env: Optional[str] = None
    rgb: Optional[str] = None

    def start(self) -> None:
        player = self.session.player

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            logger.warning("battle is not legal, won't start")
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
        current_monster.wild = True

        # Create an NPC object which will be this monster's "trainer"
        self.world = self.session.client.get_state_by_name(WorldState)
        npc = NPC("random_encounter_dummy", world=self.world)
        npc.add_monster(current_monster, len(npc.monsters))
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed

        # Lookup the environment
        env = "grass" if self.env is None else self.env
        environment = db.lookup(env, table="environment")

        self.session.client.queue_state(
            "CombatState",
            players=(player, npc),
            combat_type="monster",
            graphics=environment.battle_graphics,
        )

        # stop the player
        self.world.lock_controls()
        self.world.stop_player()

        # flash the screen
        rgb: ColorLike = prepare.WHITE_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)
        self.session.client.push_state(FlashTransition(color=rgb))

        # Start some music!
        filename = environment.battle_music
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
