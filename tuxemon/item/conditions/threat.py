# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class ThreatCondition(ItemCondition):
    """True if the property is correct."""

    name = "threat"

    def test(self, target: Monster) -> bool:
        if target.cat == "threat":
            return True
        else:
            return False
