# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import TechniqueModel, db
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session


lookup_cache: dict[str, TechniqueModel] = {}


@dataclass
class LearnMmEffect(CoreEffect):
    """
    Teaches the target a random technique of a specified element.

    Parameters:
        element: Type of element (e.g., wood, water, etc.)
    """

    name = "learn_mm"
    element: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if not lookup_cache:
            _lookup_techniques(self.element)

        known_moves = [tech.slug for tech in target.moves.get_moves()]
        available = list(set(lookup_cache.keys()) - set(known_moves))

        if available:
            tech_slug = random.choice(available)

            if target.moves.has_move(tech_slug):
                return ItemEffectResult(name=item.name)

            tech = Technique.create(tech_slug)
            target.moves.learn(target.instance_id, tech)

            return ItemEffectResult(name=item.name, success=True)

        return ItemEffectResult(name=item.name)


def _lookup_techniques(element: str) -> None:
    monsters = list(db.database["technique"])
    for mon in monsters:
        results = TechniqueModel.lookup(mon, db)
        if results.randomly and element in results.types:
            lookup_cache[mon] = results
