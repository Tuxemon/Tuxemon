# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterHealthAction(EventAction):
    """
    Set the hp of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_health [variable][,health]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters are healed.
        health: A float value between 0 and 1, which is the percent of max
            hp to be restored to. A int value, which is the number of HP
            to be restored to. If no health is specified, the hp is maxed
            out.

    """

    name = "set_monster_health"
    variable: Optional[str] = None
    health: Optional[Union[int, float]] = None

    @staticmethod
    def set_health(monster: Monster, value: Union[float, int]) -> None:
        if isinstance(value, float):
            monster.current_hp = int(monster.hp * value)
        else:
            monster.current_hp = int(value)
        # checks max and min
        if monster.current_hp <= 0:
            monster.faint()
        if monster.current_hp > monster.hp:
            monster.current_hp = monster.hp
        logger.info(f"{monster.name}'s {monster.current_hp} HP")

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return

        monster_health = 1.0 if self.health is None else self.health

        if self.variable is None:
            for mon in player.monsters:
                self.set_health(mon, monster_health)
        else:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                logger.error("Monster not found")
                return
            self.set_health(monster, monster_health)
