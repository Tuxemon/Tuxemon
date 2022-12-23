from __future__ import annotations

import random
from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class ForgetTmEffectResult(ItemEffectResult):
    pass


@dataclass
class ForgetTmEffect(ItemEffect):
    """
    This effect makes forget the technique in the parameters.
    If it uses "random", then it'll forget a random move.
    """

    name = "forget_tm"
    technique: str

    def apply(self, target: Monster) -> ForgetTmEffectResult:
        # monster moves
        moves = []

        # clean up the list
        set_moves = set(moves)
        res = list(set_moves)
        # continue operation
        if self.technique == "random":
            if len(res) > 1:
                rd = random.randint(0, len(res))
                target.moves.pop(rd)
                return {"success": True}
            else:
                return {"success": False}
        else:
            if len(target.moves) > 1:
                for tech in target.moves:
                    if tech.slug == self.technique:
                        target.moves.remove(tech)
                        return {"success": True}
                    else:
                        return {"success": False}
            else:
                return {"success": False}
