# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random as rd
import uuid
from dataclasses import dataclass
from typing import Optional, Union, final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.prepare import BOND_RANGE

logger = logging.getLogger(__name__)


@final
@dataclass
class ModifyMonsterBondAction(EventAction):
    """
    Change the bond of a monster in the current player's party.

    Script usage:
        .. code-block::

            modify_monster_bond [variable][,amount]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters are touched.
        amount: An int or float value, if no amount, then default 1 (int).

    eg. "modify_monster_bond"
    eg. "modify_monster_bond name_variable,25"
    eg. "modify_monster_bond name_variable,-0.5"
    eg. "modify_monster_bond name_variable,,1,5" (random between 1 and 5)
    eg. "modify_monster_bond name_variable,,-11,-5" (random between 1 and 5)

    """

    name = "modify_monster_bond"
    variable: Optional[str] = None
    amount: Optional[Union[int, float]] = None
    lower_bound: Optional[int] = None
    upper_bound: Optional[int] = None

    @staticmethod
    def change_bond(monster: Monster, value: Union[int, float]) -> None:
        if isinstance(value, float):
            monster.bond += int(value * monster.bond)
        else:
            monster.bond += value
        if monster.bond > BOND_RANGE[1]:
            monster.bond = BOND_RANGE[1]
        if monster.bond < BOND_RANGE[0]:
            monster.bond = BOND_RANGE[0]
        logger.info(f"{monster.name}'s bond is {monster.bond}")

    def start(self) -> None:
        player = self.session.player
        if not player.monsters:
            return

        amount_bond = self.amount if self.amount else 1
        if amount_bond == 1:
            if self.lower_bound is not None and self.upper_bound is not None:
                amount_bond = rd.randint(self.lower_bound, self.upper_bound)

        if self.variable is None:
            for mon in player.monsters:
                self.change_bond(mon, amount_bond)
        else:
            if self.variable not in player.game_variables:
                logger.error(f"Game variable {self.variable} not found")
                return
            monster_id = uuid.UUID(player.game_variables[self.variable])
            monster = get_monster_by_iid(self.session, monster_id)
            if monster is None:
                logger.error("Monster not found")
                return
            else:
                self.change_bond(monster, amount_bond)
