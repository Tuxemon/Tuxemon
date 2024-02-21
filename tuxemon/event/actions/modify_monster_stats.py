# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random as rd
import uuid
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.db import StatType
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


@final
@dataclass
class ModifyMonsterStatsAction(EventAction):
    """
    Change the stats of a monster in the current player's party.

    Script usage:
        .. code-block::

            modify_monster_stats [variable][,stat][,amount]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters are touched.
        stat: A stat among armour, dodge, hp, melee, speed and ranged. If no
            stat, then all the stats.
        amount: A/an float/int value, if no amount, then default 1 (+).

    eg. "modify_monster_stats"
    eg. "modify_monster_stats ,,0.25"
    eg. "modify_monster_stats name_variable,speed,25"
    eg. "modify_monster_stats name_variable,dodge,-12"
    eg. "modify_monster_stats name_variable,dodge,-0.4"
    eg. "modify_monster_stats name_variable,,,1,5" (random between 1 and 5)

    """

    name = "modify_monster_stats"
    variable: Optional[str] = None
    stat: Optional[str] = None
    amount: Optional[Union[float, int]] = None
    lower_bound: Optional[int] = None
    upper_bound: Optional[int] = None

    @staticmethod
    def modifiy_stat_int(monster: Monster, stat: StatType, value: int) -> None:
        logger.info(f"{value} int, operation addition")
        monster.mod_armour += value if stat == StatType.armour else 0
        monster.mod_dodge += value if stat == StatType.dodge else 0
        monster.mod_hp += value if stat == StatType.hp else 0
        monster.mod_melee += value if stat == StatType.melee else 0
        monster.mod_speed += value if stat == StatType.speed else 0
        monster.mod_ranged += value if stat == StatType.ranged else 0
        monster.set_stats()
        logger.info(f"{monster.name}'s {stat} = {value}")

    @staticmethod
    def modifiy_stat_float(
        monster: Monster, stat: StatType, value: float
    ) -> None:
        logger.info(f"{value} float, operation multiplication")
        ar_value = monster.armour * value if stat == StatType.armour else 0
        do_value = monster.dodge * value if stat == StatType.dodge else 0
        hp_value = monster.hp * value if stat == StatType.hp else 0
        me_value = monster.melee * value if stat == StatType.melee else 0
        sp_value = monster.speed * value if stat == StatType.speed else 0
        ra_value = monster.ranged * value if stat == StatType.ranged else 0
        # applies on the value
        monster.mod_armour += int(ar_value)
        monster.mod_dodge += int(do_value)
        monster.mod_hp += int(hp_value)
        monster.mod_melee += int(me_value)
        monster.mod_speed += int(sp_value)
        monster.mod_ranged += int(ra_value)
        monster.set_stats()
        logger.info(f"{monster.name}'s {stat} = {value}")

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return
        if self.stat and self.stat not in list(StatType):
            raise ValueError(f"{self.stat} isn't among {list(StatType)}")

        monster_stats = [StatType(self.stat)] if self.stat else list(StatType)
        amount_stat = 1 if self.amount is None else self.amount
        if amount_stat == 1:
            if self.lower_bound is not None and self.upper_bound is not None:
                amount_stat = rd.randint(self.lower_bound, self.upper_bound)

        if self.variable is None:
            for mon in player.monsters:
                for stat in monster_stats:
                    if isinstance(amount_stat, float):
                        self.modifiy_stat_float(mon, stat, amount_stat)
                    else:
                        self.modifiy_stat_int(mon, stat, amount_stat)
        else:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                logger.error("Monster not found")
                return
            for stat in monster_stats:
                if isinstance(amount_stat, float):
                    self.modifiy_stat_float(monster, stat, amount_stat)
                else:
                    self.modifiy_stat_int(monster, stat, amount_stat)
