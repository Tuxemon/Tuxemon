# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class GiveExperienceAction(EventAction):
    """
    Gives experience points to the monster.

    Script usage:
        .. code-block::

            give_experience <variable>,<exp>

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters get experience.
        exp: Name of the variable where to store the experience points or
            directly the number of points. Negative value will result in 0.

    eg. "give_experience name_variable,steps_variable"
    eg. "give_experience name_variable,420"

    """

    name = "give_experience"
    variable: Optional[str] = None
    exp: Optional[str] = None

    def start(self) -> None:
        player = self.session.player

        self.exp = "0" if self.exp is None else self.exp
        if self.exp.isdigit():
            exp = int(self.exp)
        else:
            exp = int(player.game_variables.get(self.exp, 0))

        exp = 0 if exp < 0 else exp

        if self.variable is None:
            monsters = player.monsters
        else:
            variable = self.variable
            if variable not in player.game_variables:
                return

            monster_id = uuid.UUID(player.game_variables[variable])
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                monster = player.monster_boxes.get_monsters_by_iid(monster_id)
                if monster is None:
                    logger.error("Monster not found")
                    return
            monsters = [monster]

        if monsters:
            for mon in monsters:
                level = mon.give_experience(exp)
                logger.info(f"{mon.name} +{exp} exp")
                if level > 0:
                    mon.update_moves(level)
                    logger.info(f"{mon.name} +{level} levels")
