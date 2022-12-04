from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemcondition import ItemCondition
from tuxemon.monster import Monster


@dataclass
class HasPathCondition(ItemCondition):
    """
    Checks against the creature's evolution paths.

    Accepts a single parameter and returns whether it is applied.

    """

    name = "has_path"
    expected: str

    def test(self, target: Monster) -> bool:
        if any(t for t in target.evolutions if t.item == self.expected):
            return True
        else:
            return False
