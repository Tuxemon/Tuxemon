# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random as rd
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

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
        lower_bound: Lower bound of range to return an integer between (inclusive)
        upper_bound: Upper bound of range to return an integer between (inclusive)

    eg. "modify_monster_bond"
    eg. "modify_monster_bond name_variable,25"
    eg. "modify_monster_bond name_variable,-0.5"
    eg. "modify_monster_bond name_variable,,1,5" (random between 1 and 5)
    eg. "modify_monster_bond name_variable,,-5,-1" (random between -5 and -1)
    """

    name = "modify_monster_bond"
    variable: str | None = None
    amount: int | float | None = None
    lower_bound: int | None = None
    upper_bound: int | None = None

    def start(self, session: Session) -> None:
        player = session.player
        if not player.monsters:
            self.stop()
            return

        amount_bond = self.amount if self.amount else 1
        if (
            amount_bond == 1
            and self.lower_bound is not None
            and self.upper_bound is not None
        ):
            amount_bond = rd.randint(self.lower_bound, self.upper_bound)

        if self.variable is None:
            for mon in player.monsters:
                floor = mon.bond_handler.get_effective_min_bond(mon.stage)
                crossed = mon.bond_handler.change_bond(amount_bond, floor)
                if crossed:
                    logger.debug(
                        f"{mon.name} crossed bond milestones: {crossed}"
                    )
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
            else:
                floor = monster.bond_handler.get_effective_min_bond(
                    monster.stage
                )
                crossed = monster.bond_handler.change_bond(amount_bond, floor)
                if crossed:
                    logger.debug(
                        f"{monster.name} crossed bond milestones: {crossed}"
                    )
