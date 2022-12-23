from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.db import ElementType, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class LearnMmEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnMmEffect(ItemEffect):
    """This effect teaches the target a random type technique."""

    name = "learn_mm"
    element: ElementType

    def apply(self, target: Monster) -> LearnMmEffectResult:
        techs = list(db.database["technique"])
        # type moves
        filters = []
        for mov in techs:
            results = db.lookup(mov, table="technique")
            if self.element in results.types:
                filters.append(results.slug)
        # monster moves
        moves = []
        for tech in target.moves:
            moves.append(tech.slug)
        # remove monster moves from type moves
        set1 = set(filters)
        set2 = set(moves)
        res = list(set1 - set2)
        # add a random move from what remains
        if res:
            self.user.game_variables["overwrite_technique"] = random.choice(
                res
            )
            return {"success": True}
        else:
            return {"success": False}
