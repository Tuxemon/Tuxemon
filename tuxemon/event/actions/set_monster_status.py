# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.status.status import Status

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
    variable: Optional[str] = None
    status: Optional[str] = None

    @staticmethod
    def set_status(
        monster: Monster, value: Optional[str], steps: float
    ) -> None:
        if not value:
            monster.status = list()
        else:
            status = Status()
            status.load(value)
            status.steps = steps
            status.link = monster
            monster.apply_status(status)

    def start(self) -> None:
        player = self.session.player
        steps = player.steps
        if not player.monsters:
            return

        if self.variable is None:
            for mon in player.monsters:
                self.set_status(mon, self.status, steps)
        else:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                logger.error("Monster not found")
                return
            self.set_status(monster, self.status, steps)
