# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.combat.combat_context import (
    BattleMode,
    CombatContext,
    CombatType,
)
from tuxemon.combat.utils import check_battle_legal
from tuxemon.database.rules import config_monster
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel, NpcModel
from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.platform.const.sizes import PARTY_LIMIT
from tuxemon.session import Session

logger = logging.getLogger(__name__)


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
        MonsterModel.load_cache(db)
        self.monster_cache = MonsterModel.get_cache()

        NpcModel.load_cache(db)
        self.npc_cache = NpcModel.get_cache()

        self._validate_parameters()
        self._prepare_opponent(session)
        self._start_battle(session)

    def _validate_parameters(self) -> None:
        if not (1 <= self.nr_txmns <= PARTY_LIMIT):
            raise ValueError(
                f"Party size {self.nr_txmns} must be between 1 and {PARTY_LIMIT}"
            )
        if not (1 <= self.max_level <= config_monster.level_range[1]):
            raise ValueError(
                f"Max level {self.max_level} must be between 1 and {config_monster.level_range[1]}"
            )

    def _prepare_opponent(self, session: Session) -> None:

        lookup_cache_npc = {
            slug: npc
            for slug, npc in self.npc_cache.items()
            if not npc.monsters
        }

        if not lookup_cache_npc:
            raise ValueError("No valid NPCs found to start a random battle.")
        if not self.monster_cache:
            raise ValueError(
                "No valid monsters found to start a random battle."
            )

        self.opponent = random.choice(list(lookup_cache_npc.values()))
        session.client.event_engine.execute_action(
            "create_npc", [self.opponent.slug, 0, 0], True
        )

    def _start_battle(self, session: Session) -> None:
        npc = session.client.get_npc(self.opponent.slug)
        if npc is None:
            logger.error(f"{self.opponent.slug} not found after creation.")
            self.stop()
            return

        monster_filters = list(self.monster_cache.values())

        if self.nr_txmns > len(monster_filters):
            logger.error(
                "Not enough monsters available to form the requested party."
            )

        monsters_to_add = random.sample(monster_filters, self.nr_txmns)
        for monster in monsters_to_add:
            level = random.randint(self.min_level, self.max_level)
            spawn_monster = Monster.spawn_base(monster.slug, level)
            spawn_monster.money_modifier = level
            spawn_monster.set_experience_modifier(level)
            npc.party.insert_monster_to_party(spawn_monster, len(npc.monsters))

        player = session.player
        if not (check_battle_legal(player) and check_battle_legal(npc)):
            logger.warning("Battle is not legal, won't start.")
            self.stop()
            return

        environment = session.client.environment_manager
        env = environment.get_active_environment()
        if env is None:
            logger.error(
                "No environment defined. Use 'set_environment' before starting combat."
            )
            self.stop()
            return

        logger.info(f"Starting battle with '{npc.name}'!")
        context = CombatContext(
            session=session,
            teams=[player, npc],
            combat_type=CombatType.TRAINER,
            battle_mode=BattleMode.SINGLE,
        )
        session.client.push_state("CombatState", context=context)
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
        if self.opponent:
            session.client.npc_manager.remove_npc(self.opponent.slug)
