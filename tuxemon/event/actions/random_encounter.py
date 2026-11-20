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
from tuxemon.combat.utils import check_battle_legal, check_repellent
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster
from tuxemon.platform.const.graphics import WHITE_COLOR
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RandomEncounterAction(EventAction):
    """
    Randomly start an encounter.

    Randomly starts a battle with a monster defined in the "encounter" table
    in the "monster.db" database. The chance that this will start a battle
    depends on the "encounter_rate" specified in the database. The
    "encounter_rate" number is the chance
    walking in to this tile will trigger a battle out of 100.
    "total_prob" is an optional override which scales the probabilities so
    that the sum is equal to "total_prob".

    Script usage:
        .. code-block::

            random_encounter <encounter_slug>[,total_prob][,rgb]

    Script parameters:
        encounter_slug: Slug of the encounter list.
        total_prob: Total sum of the probabilities.
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(255,255,255)
    """

    name = "random_encounter"
    encounter_slug: str
    total_prob: float | None = None
    rgb: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        environment = session.client.environment_manager
        encounter = session.client.encounter_manager

        if not check_battle_legal(player):
            logger.error("Battle is not legal, won't start")
            self.stop()
            return

        if check_repellent(player):
            logger.info("Repellent active, skipping encounter.")
            self.stop()
            return

        if not encounter.load_zone(self.encounter_slug):
            self.stop()
            return

        total_prob = self.total_prob if self.total_prob else 1.0
        results = encounter.attempt_single_encounter(player, total_prob)

        if results is None:
            self.stop()
            return

        logger.info("Starting random encounter!")

        current_monster = Monster.spawn_base(
            results.monster.monster, results.level
        )
        current_monster.set_experience_modifier(results.monster.exp_req_mod)

        if results.held_item is not None:
            item = Item.create(results.held_item)
            output = current_monster.equip_item(item)
            if not output:
                self.stop()
                return

        current_monster.wild = True

        event_engine = session.client.event_engine
        event_engine.execute_action(
            "create_npc", ["wild_encounter", 0, 0], True
        )

        npc = session.client.get_npc("wild_encounter")
        if npc is None:
            logger.error("'wild_encounter' not found")
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
        session.client.npc_manager.remove_npc("wild_encounter")
