# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid

from tuxemon.event import MapCondition, get_monster_by_iid
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


class ScoopCondition(EventCondition):
    """
    Calculate the value of the monster.
    How much the player can get by selling its monster?

    Script usage:
        .. code-block::

            is scoop variable

    Script parameters:
        variable: Name of the variable where to store the monster id.

    """

    name = "scoop"

    def test(self, session: Session, condition: MapCondition) -> bool:
        player = session.player
        variable = condition.parameters[0]

        if variable not in player.game_variables:
            logger.error(f"Game variable {variable} not found")
            return False

        monster_id = uuid.UUID(player.game_variables[variable])
        monster = get_monster_by_iid(session, monster_id)
        if monster is None:
            logger.error(f"{variable} not found")
            return False

        _scoop_price = f"{self.name}_price"
        _price = player.game_variables.get(_scoop_price, 0)
        _scoop_coeff = f"{self.name}_coeff"
        _coeff = player.game_variables.get(_scoop_coeff, 0)

        price = 0
        price += monster.level * int(_coeff)
        if price != _price:
            player.game_variables[_scoop_price] = price
        return True
