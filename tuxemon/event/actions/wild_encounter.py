# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.combat.combat_context import (
    BattleMode,
    CombatContext,
    CombatType,
)
from tuxemon.combat.utils import check_battle_legal
from tuxemon.db import EnvironmentModel, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.item.item import Item
from tuxemon.monster import Monster
from tuxemon.session import Session

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

        current_monster = Monster.spawn_base(
            self.monster_slug, self.monster_level
        )
        if self.exp is not None:
            current_monster.set_experience_modifier(self.exp)
        if self.money is not None:
            current_monster.money_modifier = self.money
        if self.held_item is not None:
            item = Item.create(self.held_item)
            output = current_monster.item_handler.set_item(item)
            if not output:
                return
        current_monster.wild = True

        event_engine = session.client.event_engine
        event_engine.execute_action("create_npc", [self.name, 0, 0], True)

        npc = get_npc(session, self.name)
        if npc is None:
            logger.error(f"{self.name} not found")
            return

        npc.party.insert_monster_to_party(current_monster, len(npc.monsters))
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed

        env_var = player.game_variables.get("environment", "grass")
        env = env_var if self.env is None else self.env
        environment = EnvironmentModel.lookup(env, db)

        context = CombatContext(
            session=session,
            teams=[player, npc],
            combat_type=CombatType.MONSTER,
            graphics=environment.battle_graphics,
            music=environment.battle_music,
            battle_mode=BattleMode.SINGLE,
        )
        session.client.queue_state("CombatState", context=context)

        session.client.movement_manager.lock_controls(player)
        session.client.movement_manager.stop_char(player)

        rgb: ColorLike = prepare.WHITE_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)
        session.client.push_state("FlashTransition", color=rgb)

        sound = environment.battle_music.battle
        if sound.music:
            session.client.current_music.play(sound.music, sound.volume)

    def update(self, session: Session, dt: float) -> None:
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
