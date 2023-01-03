# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster


class LearnTmEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnTmEffect(ItemEffect):
    """This effect teaches the target the technique in the parameters."""

    name = "learn_tm"
    technique: str

    def apply(self, target: Monster) -> LearnTmEffectResult:
        # monster moves
        moves = []
        for tech in target.moves:
            moves.append(tech.slug)
        # clean up the list
        set_moves = set(moves)
        res = list(set_moves)
        # continue operation
        if res:
            if self.technique in res:
                return {"success": False}
            else:
                self.user.game_variables[
                    "overwrite_technique"
                ] = self.technique
                return {"success": True}
        else:
            return {"success": False}
