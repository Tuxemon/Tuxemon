# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.item.itemcondition import ItemCondition

if TYPE_CHECKING:
    from tuxemon.monster import Monster


@dataclass
class CanEvolveCondition(ItemCondition):
    """
    Checks if the target Monster meets its evolution criteria.

    This condition evaluates whether the Monster's current state matches
    its evolution requirements.
    """

    name = "can_evolve"

    def test(self, target: Monster) -> bool:
        context = {
            "map_inside": self.session.client.map_inside,
            "use_item": True,
        }
        if not target.evolutions:
            return False
        for evolution in target.evolutions:
            if target.evolution_handler.can_evolve(
                evolution_item=evolution, context=context
            ):
                return True
        return False
