# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class DaycareAction(EventAction):
    """
    Daycare checks and creates variable related to the Daycare activity.

    Script usage:
        .. code-block::

            is daycare <variable>[,release]

    Script parameters:
        variable: Name of the variable where to store the monster id.
        steps: Name of the variable where to store the nr of steps.
        release: Whether will be release or not.

    eg. "daycare name_variable,steps_variable"

    """

    name = "daycare"
    variable: str
    steps: str
    release: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        variable = self.variable
        if variable not in player.game_variables:
            return

        monster_id = uuid.UUID(player.game_variables[variable])
        monster = player.find_monster_in_storage(monster_id)
        if monster:
            player.game_variables[f"{self.name}_name"] = monster.name
            _steps = player.game_variables.get(self.steps, 0)
            diff = player.steps - int(float(_steps))
            player.game_variables[f"{self.name}_exp"] = int(diff)
            if self.release:
                level = monster.give_experience(int(diff))
                player.game_variables[f"{self.name}_level"] = level
                if level > 0:
                    monster.update_moves(level)
                    logger.info(f"{monster.name} +{level} levels")
                else:
                    logger.info(f"{monster.name} +{diff} exp")
