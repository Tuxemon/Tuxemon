# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import PlagueType
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterPlagueAction(EventAction):
    """
    Cure or infect a monster.

    Script usage:
        .. code-block::

            set_monster_plague <variable>,<condition>

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters get the condition.
        condition: inoculated, healthy or infected, default healthy

    """

    name = "set_monster_plague"
    variable: Optional[str] = None
    condition: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return
        if self.condition is None:
            self.condition = PlagueType.healthy
        if self.condition not in list(PlagueType):
            raise ValueError(
                f"{self.condition} must be inoculated, infected or healthy"
            )

        if self.variable is None:
            for mon in player.monsters:
                mon.plague = PlagueType(self.condition)
        else:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = player.find_monster_by_id(monster_id)
            if monster is None:
                logger.error("Monster not found in party")
                return
            monster.plague = PlagueType(self.condition)
