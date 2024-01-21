# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.db import ElementType, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class LearnMmEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnMmEffect(ItemEffect):
    """
    This effect teaches the target a random type technique.

    Parameters:
        element: type of element (wood, water, etc.)

    """

    name = "learn_mm"
    element: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> LearnMmEffectResult:
        learn: bool = False
        element = ElementType(self.element)
        techs = list(db.database["technique"])
        filters: list[str] = []
        for mov in techs:
            results = db.lookup(mov, table="technique")
            if results.randomly and element in results.types:
                filters.append(results.slug)
        moves = [tech.slug for tech in target.moves] if target else []
        _techs = list(set(filters) - set(moves))
        client = self.session.client
        if _techs and target:
            tech_slug = random.choice(_techs)
            var = f"{self.name}:{str(target.instance_id.hex)}"
            client.event_engine.execute_action("set_variable", [var], True)
            client.event_engine.execute_action(
                "add_tech", [self.name, tech_slug], True
            )
            learn = True
        return {"success": learn, "num_shakes": 0, "extra": None}
