# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
        moves = [tech.slug for tech in target.moves] if target else []
        moves = list(set(moves))
        client = self.session.client
        if target and moves and self.technique not in moves:
            var = f"{self.name}:{str(target.instance_id.hex)}"
            client.event_engine.execute_action("set_variable", [var], True)
            client.event_engine.execute_action(
                "add_tech", [self.name, self.technique], True
            )
            learn = True
        return {"success": learn, "num_shakes": 0, "extra": None}
