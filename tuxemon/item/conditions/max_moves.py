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
    max_moves: str

    def test(self, target: Monster) -> bool:
        if len(target.moves) > MAX_MOVES:
            return False
        else:
            return True
