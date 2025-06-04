# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.item.item import Item
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class WildEncounterAction(EventAction):
    """
    Start a encounter with a single wild monster.

    Script usage:
        .. code-block::

            wild_encounter <monster_slug>,<monster_level>[,exp_mod]
                            [,mon_mod][,env][,rgb][,held_item]

    Script parameters:
        monster_slug: Monster slug.
        monster_level: Level of monster.
        exp_mod: Experience modifier.
        mon_mod: Money modifier.
        env: Environment (grass default)
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(255,255,255)
        held_item: item held by the monster
    """

    name = "wild_encounter"
    monster_slug: str
    monster_level: int
    exp: Optional[float] = None
    money: Optional[float] = None
    env: Optional[str] = None
    rgb: Optional[str] = None
    held_item: Optional[str] = None

    def start(self, session: Session) -> None:
        player = session.player

        if not check_battle_legal(player):
            logger.warning("battle is not legal, won't start")
            return

        logger.info("Starting wild encounter!")

        current_monster = Monster.create(self.monster_slug)
        current_monster.level = self.monster_level
        current_monster.set_level(self.monster_level)
        current_monster.moves.set_moves(self.monster_level)
        current_monster.current_hp = current_monster.hp
        if self.exp is not None:
            current_monster.experience_modifier = self.exp
        if self.money is not None:
            current_monster.money_modifier = self.money
        if self.held_item is not None:
            item = Item.create(self.held_item)
            if item.behaviors.holdable:
                current_monster.held_item.set_item(item)
            else:
                logger.error(f"{item.name} isn't 'holdable'")
        current_monster.wild = True

        event_engine = session.client.event_engine
        event_engine.execute_action("create_npc", [self.name, 0, 0], True)

        npc = get_npc(session, self.name)
        if npc is None:
            logger.error(f"{self.name} not found")
            return

        npc.add_monster(current_monster, len(npc.monsters))
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed

        env_var = player.game_variables.get("environment", "grass")
        env = env_var if self.env is None else self.env
        environment = db.lookup(env, table="environment")

        player.tuxepedia.add_entry(current_monster.slug)

        session.client.queue_state(
            "CombatState",
            session=session,
            players=(player, npc),
            combat_type="monster",
            graphics=environment.battle_graphics,
            battle_mode="single",
        )

        self.world = session.client.get_state_by_name(WorldState)
        self.world.movement.lock_controls(player)
        self.world.movement.stop_char(player)

        rgb: ColorLike = prepare.WHITE_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)
        session.client.push_state("FlashTransition", color=rgb)

        session.client.event_engine.execute_action(
            "play_music", [environment.battle_music], True
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_queued_state_by_name("CombatState")
        except ValueError:
            try:
                session.client.get_state_by_name("CombatState")
            except ValueError:
                self.stop()

    def cleanup(self, session: Session) -> None:
        npc = None
        session.client.npc_manager.remove_npc(self.name)
