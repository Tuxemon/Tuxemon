# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class LearnTmEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnTmEffect(ItemEffect):
    """
    This effect teaches the technique in the parameters.

    Parameters:
        technique: technique's slug (eg. ram, etc.)

    """

    name = "learn_tm"
    technique: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> LearnTmEffectResult:
        learn: bool = False
        assert target
        # monster moves
        moves = []
        for tech in target.moves:
            moves.append(tech.slug)
        # clean up the list
        set_moves = set(moves)
        res = list(set_moves)
        # continue operation
        if res:
            if self.technique not in res:
                self.user.game_variables[
                    "overwrite_technique"
                ] = self.technique
                learn = True
        return {"success": learn, "num_shakes": 0, "extra": None}
