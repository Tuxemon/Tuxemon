# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.db import TechniqueModel, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


lookup_cache: dict[str, TechniqueModel] = {}


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
    ) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_techniques(self.element)

        moves = [tech.slug for tech in target.moves] if target else []

        available = list(set(list(lookup_cache.keys())) - set(moves))

        if available and target:
            tech_slug = random.choice(available)

            client = self.session.client
            var = f"{self.name}:{str(target.instance_id.hex)}"
            client.event_engine.execute_action("set_variable", [var], True)
            client.event_engine.execute_action(
                "add_tech", [self.name, tech_slug], True
            )

            return ItemEffectResult(
                name=item.name, success=True, num_shakes=0, extras=[]
            )

        return ItemEffectResult(
            name=item.name, success=False, num_shakes=0, extras=[]
        )


def _lookup_techniques(element: str) -> None:
    monsters = list(db.database["technique"])
    for mon in monsters:
        results = db.lookup(mon, table="technique")
        if results.randomly and element in results.types:
            lookup_cache[mon] = results
