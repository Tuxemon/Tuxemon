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

        if self.total_prob is not None:
            if not (0 <= self.total_prob <= 100):
                logger.error(
                    f"Invalid total_prob: {self.total_prob}. Must be between 0 and 100."
                )
                self.stop()
                return

        if not encounter.load_zone(self.encounter_slug):
            self.stop()
            return

        results = encounter.attempt_horde_encounter(player, self.total_prob)

        if not results:
            self.stop()
            return

        logger.info("Starting random horde!")

        horde: list[Monster] = []

        for result in results.monsters:
            current_monster = Monster.spawn_base(
                result.monster.monster, result.level
            )
            base_mod = result.monster.exp_req_mod
            horde_mod = results.horde_exp_mod or 1.0
            final_mod = base_mod * horde_mod
            current_monster.set_experience_modifier(final_mod)

            if result.held_item is not None:
                item = Item.create(result.held_item)
                output = current_monster.equip_item(item)
                if not output:
                    self.stop()
                    return

                current_monster.wild = True

            horde.append(current_monster)

        if not horde:
            self.stop()
            return

        event_engine = session.client.event_engine
        event_engine.execute_action(
            "create_npc", ["wild_encounter", 0, 0], True
        )

        npc = session.client.get_npc("wild_encounter")
        if npc is None:
            logger.error("'wild_encounter' not found")
            self.stop()
            return

        npc.party.replace_party(
            horde,
            add_overflow_to_box=False,
            override_policy_name="unlimited_party",
        )
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
            combat_type=CombatType.HORDE,
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
