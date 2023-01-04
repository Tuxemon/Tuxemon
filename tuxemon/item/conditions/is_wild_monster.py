# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class IsWildMonsterCondition(ItemCondition):
    """True if not owned by a trainer."""

    name = "is_wild_monster"

    def test(self, target: Monster) -> bool:
        return target.owner is None
