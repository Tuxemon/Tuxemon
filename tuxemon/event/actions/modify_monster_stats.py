# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random as rd
import uuid
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.db import StatType
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.formula import modify_stat
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
        lower_bound: Lower bound of range to return an integer between (inclusive)
        upper_bound: Upper bound of range to return an integer between (inclusive)

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
    amount: Optional[Union[int, float]] = None
    lower_bound: Optional[int] = None
    upper_bound: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return
        if self.stat and self.stat not in list(StatType):
            raise ValueError(f"{self.stat} isn't among {list(StatType)}")

        monster_stats = [StatType(self.stat)] if self.stat else list(StatType)
        amount_stat = 1 if self.amount is None else self.amount

        if (
            amount_stat == 1
            and self.lower_bound is not None
            and self.upper_bound is not None
        ):
            amount_stat = rd.randint(self.lower_bound, self.upper_bound)

        def modify_monster_stat(
            monster: Monster, stat: StatType, amount: float
        ) -> None:
            method = "multiply" if isinstance(amount, float) else "add"
            modify_stat(monster, stat.value, amount, method)

        if self.variable is None:
            for mon in player.monsters:
                for stat in monster_stats:
                    modify_monster_stat(mon, stat, amount_stat)
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
                modify_monster_stat(monster, stat, amount_stat)
