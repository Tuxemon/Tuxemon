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
from tuxemon.combat.utils import check_battle_legal, check_repellent
from tuxemon.db import EnvironmentModel, db
from tuxemon.encounter import Encounter, EncounterData
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import ColorLike, string_to_colorlike
from tuxemon.item.item import Item
from tuxemon.monster import Monster
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
    total_prob: Optional[float] = None
    rgb: Optional[str] = None

    def start(self, session: Session) -> None:
        player = session.player

        if not check_battle_legal(player):
            logger.error("Battle is not legal, won't start")
            return

        if check_repellent(player):
            logger.info(f"Repellent active, skipping encounter.")
            return

        zone = EncounterData(self.encounter_slug)
        encounter = Encounter(zone)
        total_prob = self.total_prob if self.total_prob else 1.0
        results = encounter.get_single_encounter(player, total_prob)

        if results is None:
            return

        eligible, level, held_item = results

        logger.info("Starting random encounter!")

        current_monster = Monster.spawn_base(eligible.monster, level)
        current_monster.set_experience_modifier(eligible.exp_req_mod)

        if held_item is not None:
            item = Item.create(held_item)
            output = current_monster.item_handler.set_item(item)
            if not output:
                return

        current_monster.wild = True

        event_engine = session.client.event_engine
        event_engine.execute_action(
            "create_npc", ["wild_encounter", 0, 0], True
        )

        npc = get_npc(session, "wild_encounter")
        if npc is None:
            logger.error("'wild_encounter' not found")
            return

        npc.party.insert_monster_to_party(current_monster, len(npc.monsters))
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed

        env = player.game_variables.get("environment", "grass")
        environment = EnvironmentModel.lookup(env, db)

        context = CombatContext(
            session=session,
            teams=[player, npc],
            combat_type=CombatType.MONSTER,
            graphics=environment.battle_graphics,
            battle_mode=BattleMode.SINGLE,
        )
        session.client.queue_state("CombatState", context=context)

        session.client.movement_manager.lock_controls(player)
        session.client.movement_manager.stop_char(player)

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
        session.client.npc_manager.remove_npc("wild_encounter")
