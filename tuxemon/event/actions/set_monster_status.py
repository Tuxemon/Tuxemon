# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.status.status import Status
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterStatusAction(EventAction):
    """
    Change the status of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_status [slot][,status]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters get/lose status.
        status: Status to set. If no status is specified, the status is
            cleared.
    """

    name = "set_monster_status"
    variable: str | None = None
    status: str | None = None

    @staticmethod
    def set_status(
        session: Session, monster: Monster, value: str | None, steps: float
    ) -> None:
        if not value:
            monster.status.clear_status(session)
        else:
            status = Status.create(value, monster, steps)
            monster.status.add_status(status)

    def start(self, session: Session) -> None:
        player = session.player
        steps = player.steps
        if not player.monsters:
            self.stop()
            return

        if self.variable is None:
            for mon in player.monsters:
                self.set_status(session, mon, self.status, steps)
        else:
            monster_id = get_valid_uuid(player.game_variables, self.variable)
            if monster_id is None:
                logger.info(
                    f"No valid monster selected for variable '{self.variable}'"
                )
                self.stop()
                return  # Exit early if no valid UUID
            monster = session.client.get_monster_by_iid(monster_id)
            if monster is None:
                logger.error("Monster not found")
                self.stop()
                return
            self.set_status(session, monster, self.status, steps)
