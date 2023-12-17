# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterHealthAction(EventAction):
    """
    Change the hp of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_health [variable][,health]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters are healed.
        health: A float value between 0 and 1, which is the percent of max
            hp to be restored to. If no health is specified, the hp is maxed
            out.

    """

    name = "set_monster_health"
    variable: Optional[str] = None
    health: Optional[float] = None

    @staticmethod
    def set_health(monster: Monster, value: Optional[float]) -> None:
        if value is None:
            monster.current_hp = monster.hp
        else:
            if not 0 <= value <= 1:
                raise ValueError("monster health must between 0 and 1")

            monster.current_hp = int(monster.hp * value)

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return

        monster_health = self.health

        if self.variable is None:
            for mon in player.monsters:
                self.set_health(mon, monster_health)
        else:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = player.find_monster_by_id(monster_id)
            if monster is None:
                logger.error("Monster not found in party")
                return
            self.set_health(monster, monster_health)
