# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon import prepare
from tuxemon.combat.combat_context import (
    BattleMode,
    CombatContext,
    CombatType,
)
from tuxemon.combat.utils import check_battle_legal
from tuxemon.db import EnvironmentModel, MonsterModel, NpcModel, db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.session import Session
from tuxemon.time_handler import today_ordinal

logger = logging.getLogger(__name__)

lookup_cache_mon: dict[str, MonsterModel] = {}
lookup_cache_npc: dict[str, NpcModel] = {}


@final
@dataclass
class RandomBattleAction(EventAction):
    """
    Starts a random battle with a randomly chosen NPC and a party of randomly
    generated monsters within a specified level range.

    Script usage:
        .. code-block::

            random_battle nr_txmns,min_level,max_level

    Script parameters:
        nr_txmns: The number of Tuxemon in the opponent's party (1 to 6).
        min_level: The minimum level for the opponent's monsters.
        max_level: The maximum level for the opponent's monsters.
    """

    name = "random_battle"
    nr_txmns: int
    min_level: int
    max_level: int

    def start(self, session: Session) -> None:
        self._validate_parameters()
        self._prepare_opponent(session)
        self._start_battle(session)

    def _validate_parameters(self) -> None:
        if not (1 <= self.nr_txmns <= prepare.PARTY_LIMIT):
            raise ValueError(
                f"Party size {self.nr_txmns} must be between 1 and {prepare.PARTY_LIMIT}"
            )
        if not (1 <= self.max_level <= prepare.MAX_LEVEL):
            raise ValueError(
                f"Max level {self.max_level} must be between 1 and {prepare.MAX_LEVEL}"
            )

    def _prepare_opponent(self, session: Session) -> None:
        if not lookup_cache_npc or not lookup_cache_mon:
            _lookup()

        if not lookup_cache_npc:
            raise ValueError("No valid NPCs found to start a random battle.")
        if not lookup_cache_mon:
            raise ValueError(
                "No valid monsters found to start a random battle."
            )

        self.opponent = random.choice(list(lookup_cache_npc.values()))
        session.client.event_engine.execute_action(
            "create_npc", [self.opponent.slug, 0, 0], True
        )

    def _start_battle(self, session: Session) -> None:
        npc = get_npc(session, self.opponent.slug)
        if npc is None:
            logger.error(f"{self.opponent.slug} not found after creation.")
            return

        monster_filters = list(lookup_cache_mon.values())

        if self.nr_txmns > len(monster_filters):
            logger.error(
                "Not enough monsters available to form the requested party."
            )

        monsters_to_add = random.sample(monster_filters, self.nr_txmns)
        for monster in monsters_to_add:
            level = random.randint(self.min_level, self.max_level)
            current_monster = Monster.spawn_base(monster.slug, level)
            current_monster.set_capture(today_ordinal())
            current_monster.money_modifier = level
            current_monster.experience_modifier = level
            npc.party.add_monster(current_monster, len(npc.monsters))

        player = session.player
        if not (check_battle_legal(player) and check_battle_legal(npc)):
            logger.warning("Battle is not legal, won't start.")
            return

        env_slug = player.game_variables.get("environment", "grass")
        env = EnvironmentModel.lookup(env_slug, db)

        logger.info(f"Starting battle with '{npc.name}'!")
        context = CombatContext(
            session=session,
            teams=[player, npc],
            combat_type=CombatType.TRAINER,
            graphics=env.battle_graphics,
            battle_mode=BattleMode.SINGLE,
        )
        session.client.push_state("CombatState", context=context)
        session.client.event_engine.execute_action(
            "play_music", [env.battle_music], True
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("CombatState")
        except ValueError:
            self.stop()

    def cleanup(self, session: Session) -> None:
        if self.opponent:
            session.client.npc_manager.remove_npc(self.opponent.slug)


def _lookup() -> None:
    global lookup_cache_mon, lookup_cache_npc

    lookup_cache_mon = {
        mon_slug: mon_model
        for mon_slug in db.database["monster"]
        if (mon_model := MonsterModel.lookup(mon_slug, db)).txmn_id > 0
        and mon_model.randomly
    }

    lookup_cache_npc = {
        npc_slug: npc_model
        for npc_slug in db.database["npc"]
        if not (npc_model := NpcModel.lookup(npc_slug, db)).monsters
    }
