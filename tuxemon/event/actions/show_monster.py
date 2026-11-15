# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger()


@final
@dataclass
class ShowMonsterAction(EventAction):
    """
    Change to MonsterInfoState.

    This action transitions to the MonsterInfoState, displaying detailed
    information about a specific monster.

    Script usage:
        .. code-block::

            monster_info_state <monster_variable>

    Script parameters:
        monster_variable: The name of the game variable holding the monster's UUID.
    """

    name = "show_monster"
    monster_variable: str

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name == "MonsterInfoState":
            logger.error(
                "The state 'MonsterInfoState' is already active. No action taken."
            )
            self.stop()
            return

        monster = self._retrieve_monster(session)
        if monster is None:
            logger.error("Monster not found for MonsterInfoState.")
            self.stop()
            return

        params = {"monster": monster, "source": self.name}
        self.client.push_state("MonsterInfoState", **params)

    def update(self, session: Session, dt: float) -> None:
        if "MonsterInfoState" not in session.client.active_state_names:
            self.stop()

    def _retrieve_monster(self, session: Session) -> Monster | None:
        """Retrieve a monster from the game database."""
        player = session.player
        monster_id = get_valid_uuid(
            player.game_variables, self.monster_variable
        )
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.monster_variable}'"
            )
            return None
        return session.client.get_monster_by_iid(monster_id)
