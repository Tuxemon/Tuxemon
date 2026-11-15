# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.combat.combat_context import (
    BattleMode,
    CombatContext,
    CombatType,
)
from tuxemon.combat.utils import check_battle_legal
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster
from tuxemon.platform.const.graphics import WHITE_COLOR
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
                            [,mon_mod][,rgb][,held_item]

    Script parameters:
        monster_slug: Monster slug.
        monster_level: Level of monster.
        exp_mod: Experience modifier.
        mon_mod: Money modifier.
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(255,255,255)
        held_item: item held by the monster
    """

    name = "wild_encounter"
    monster_slug: str
    monster_level: int
    exp: float | None = None
    money: float | None = None
    env: str | None = None
    rgb: str | None = None
    held_item: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        environment = session.client.environment_manager

        if not check_battle_legal(player):
            logger.warning("battle is not legal, won't start")
            self.stop()
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
            output = current_monster.equip_item(item)
            if not output:
                self.stop()
                return
        current_monster.wild = True

        event_engine = session.client.event_engine
        event_engine.execute_action("create_npc", [self.name, 0, 0], True)

        npc = session.client.get_npc(self.name)
        if npc is None:
            logger.error(f"{self.name} not found")
            self.stop()
            return

        npc.party.insert_monster_to_party(current_monster, len(npc.monsters))
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed

        env = environment.get_active_environment()
        if env is None:
            logger.error(
                "No environment defined. Use 'set_environment' before starting combat."
            )
            self.stop()
            return

        context = CombatContext(
            session=session,
            teams=[player, npc],
            combat_type=CombatType.MONSTER,
            battle_mode=BattleMode.SINGLE,
        )
        session.client.queue_state("CombatState", context=context)
        player.cancel_movement()

        rgb: ColorLike = WHITE_COLOR
        if self.rgb:
            rgb = string_to_colorlike(self.rgb)
        session.client.push_state("FlashTransition", color=rgb)

        sound = env.get_battle_music().battle
        if sound.music:
            session.client.current_music.play(sound.music)

    def update(self, session: Session, dt: float) -> None:
        client = session.client
        if (
            "CombatState" not in client.active_state_names
            and not client.has_queued_state("CombatState")
        ):
            self.stop()

    def cleanup(self, session: Session) -> None:
        session.client.npc_manager.remove_npc(self.name)
