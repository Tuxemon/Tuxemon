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
class RandomHordeAction(EventAction):
    """
    Randomly start an horde.

    Randomly starts a battle with a monster defined in the "encounter" table
    in the "monster.db" database. The chance that this will start a battle
    depends on the "encounter_rate" specified in the database. The
    "encounter_rate" number is the chance
    walking in to this tile will trigger a battle out of 100.

    Script usage:
        .. code-block::

            random_horde <encounter_slug>[,rgb]

    Script parameters:
        encounter_slug: Slug of the encounter list.
        total_prob: Optional float between 0 and 100 representing the chance
            of triggering a horde encounter.
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(255,255,255)
    """

    name = "random_horde"
    encounter_slug: str
    total_prob: Optional[float] = None
    rgb: Optional[str] = None

    def start(self, session: Session) -> None:
        player = session.player

        if not check_battle_legal(player):
            logger.error("Battle is not legal, won't start")
            return

        if self.total_prob is not None:
            if not (0 <= self.total_prob <= 100):
                logger.error(
                    f"Invalid total_prob: {self.total_prob}. Must be between 0 and 100."
                )
                return

        zone = EncounterData(self.encounter_slug)
        encounter = Encounter(zone)
        results = encounter.get_horde_encounter(player, self.total_prob)

        if not results:
            return

        logger.info("Starting random horde!")

        horde: list[Monster] = []

        for result in results:
            eligible, level, held_item = result

            current_monster = Monster.spawn_base(eligible.monster, level)
            current_monster.set_experience_modifier(eligible.exp_req_mod)

            if held_item is not None:
                item = Item.create(held_item)
                output = current_monster.item_handler.set_item(item)
                if not output:
                    return

                current_monster.wild = True

            horde.append(current_monster)

        if not horde:
            return

        event_engine = session.client.event_engine
        event_engine.execute_action(
            "create_npc", ["wild_encounter", 0, 0], True
        )

        npc = get_npc(session, "wild_encounter")
        if npc is None:
            logger.error("'wild_encounter' not found")
            return

        npc.party.replace_party(
            horde,
            add_overflow_to_box=False,
            override_policy_name="unlimited_party",
        )
        # NOTE: random battles are implemented as trainer battles.
        #       this is a hack. remove this once trainer/random battlers are fixed

        env = player.game_variables.get("environment", "grass")
        environment = EnvironmentModel.lookup(env, db)

        context = CombatContext(
            session=session,
            teams=[player, npc],
            combat_type=CombatType.HORDE,
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
        session.client.npc_manager.remove_npc("wild_encounter")
