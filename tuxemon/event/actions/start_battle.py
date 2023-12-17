# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.combat import alive_party, check_battle_legal
from tuxemon.db import db
from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


@final
@dataclass
class StartBattleAction(EventAction):
    """
    Start a battle between two characters and switch to the combat module.

    Script usage:
        .. code-block::

            start_battle <character1>,<character2>

    Script parameters:
        character1: Either "player" or character slug name (e.g. "npc_maple").
        character2: Either "player" or character slug name (e.g. "npc_maple").

    """

    name = "start_battle"
    character1: str
    character2: Optional[str] = None

    def start(self) -> None:
        self.character2 = (
            "player" if self.character2 is None else self.character2
        )
        character1 = get_npc(self.session, self.character1)
        character2 = get_npc(self.session, self.character2)
        if not character1:
            logger.error(f"{self.character1} not found in map")
            return
        if not character2:
            logger.error(f"{self.character2} not found in map")
            return

        # check the battle is legal
        if not check_battle_legal(character1) or not check_battle_legal(
            character2
        ):
            logger.warning("battle is not legal, won't start")
            return

        # default environment
        env_slug = "grass"

        fighters = [character1, character2]
        for fighter in fighters:
            # check and trigger 2 vs 2
            if fighter.template[0].double and len(alive_party(fighter)) > 1:
                fighter.max_position = 2
            # check the human
            if fighter.isplayer:
                # update environment
                env_slug = fighter.game_variables.get("environment", "grass")

        # set the environment
        env = db.lookup(env_slug, table="environment")

        # sort the fighters, player first
        fighters = sorted(fighters, key=lambda x: not x.isplayer)

        # Add our players and setup combat
        logger.info(
            f"Starting battle between {fighters[0].name} and {fighters[1].name}!"
        )
        self.session.client.push_state(
            CombatState(
                players=(fighters[0], fighters[1]),
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
