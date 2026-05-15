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
from tuxemon.platform.const.sizes import MONSTERS_DOUBLE
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class StartDoubleBattleAction(EventAction):
    """
    Start a double battle between two characters and switch to the combat module.

    Script usage:
        .. code-block::

            start_double_battle <character1>,<character2>[,music]

    Script parameters:
        character1: Either "player" or character slug name (e.g. "npc_maple").
        character2: Either "player" or character slug name (e.g. "npc_maple").
        music: The name of the music file to play (Optional).
    """

    name = "start_double_battle"
    character1: str
    character2: str | None = None
    music: str | None = None

    def start(self, session: Session) -> None:
        self.character2 = self.character2 or "player"

        character1 = session.client.get_npc(self.character1)
        character2 = session.client.get_npc(self.character2)

        if not character1 or not character2:
            _char = self.character1 if not character1 else self.character2
            logger.error(f"Character not found in map: {_char}")
            self.stop()
            return

        if not (
            check_battle_legal(character1) and check_battle_legal(character2)
        ):
            logger.warning("Battle is not legal, won't start")
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

        fighters = sorted(
            [character1, character2], key=lambda x: not x.is_player
        )

        total_monsters = sum(len(fighter.monsters) for fighter in fighters)
        if total_monsters < MONSTERS_DOUBLE:
            logger.error(
                f"{total_monsters} monsters aren't enough to trigger a double battle ({MONSTERS_DOUBLE})"
            )
            self.stop()
            return

        logger.info(
            f"Starting double battle between {fighters[0].name} and {fighters[1].name}!"
        )
        context = CombatContext(
            session=session,
            teams=fighters,
            combat_type=CombatType.TRAINER,
            battle_mode=BattleMode.DOUBLE,
        )
        session.client.push_state("CombatState", context=context)
        # music
        sound = env.get_battle_music().battle
        if sound.music:
            filename = sound.music if not self.music else self.music
            session.client.current_music.play(filename)

    def update(self, session: Session, dt: float) -> None:
        if "CombatState" not in session.client.active_state_names:
            self.stop()
