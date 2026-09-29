# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random as rd
from dataclasses import dataclass
from typing import final

from tuxemon.db import StatType
from tuxemon.event.eventaction import EventAction
from tuxemon.formula import modify_monster_custom_stat
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

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
    variable: str | None = None
    stat: str | None = None
    amount: int | float | None = None
    lower_bound: int | None = None
    upper_bound: int | None = None

    def start(self, session: Session) -> None:
        player = session.player
        if not player.monsters:
            self.stop()
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
            modify_monster_custom_stat(monster, stat.value, amount, method)

        if self.variable is None:
            for mon in player.monsters:
                for stat in monster_stats:
                    modify_monster_stat(mon, stat, amount_stat)
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

            for stat in monster_stats:
                modify_monster_stat(monster, stat, amount_stat)
