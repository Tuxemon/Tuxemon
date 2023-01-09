# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon import formula
from tuxemon.combat import check_battle_legal
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.states.combat.combat import CombatState
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class StartBattleAction(EventAction):
    """
    Start a battle with the given npc and switch to the combat module.

    Script usage:
        .. code-block::

            start_battle <npc_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "start_battle"
    npc_slug: str

    def start(self) -> None:
        player = self.session.player

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            logger.warning("battle is not legal, won't start")
            return

        world = self.session.client.get_state_by_name(WorldState)

        npc = world.get_entity(self.npc_slug)
        assert npc
        if len(npc.monsters) == 0:
            logger.warning(
                f"npc '{self.npc_slug}' has no monsters, won't start trainer battle."
            )
            return

        # Rematch
        if self.npc_slug in player.battle_history:
            rematch = player.battle_history[self.npc_slug]
            for mon in npc.monsters:
                formula.rematch(player, npc, mon, rematch[1])

        # Lookup the environment
        env_slug = player.game_variables.get("environment", "grass")
        env = db.lookup(env_slug, table="environment")

        # Add our players and setup combat
        logger.info("Starting battle with '{self.npc_slug}'!")
        self.session.client.push_state(
            CombatState(
                players=(player, npc),
                combat_type="trainer",
                graphics=env.battle_graphics,
            )
        )

        # Start some music!
        filename = env.battle_music
        self.session.client.event_engine.execute_action(
            "play_music",
            [filename],
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(CombatState)
        except ValueError:
            self.stop()
