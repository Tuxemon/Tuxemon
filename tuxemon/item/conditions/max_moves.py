# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import MAX_MOVES, Monster


@dataclass
class MaxMovesCondition(ItemCondition):
    """
    Checks max moves against the creature's moves.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "max_moves"

    def test(self, target: Monster) -> bool:
        if len(target.moves) < MAX_MOVES:
            return True
        else:
            return False
