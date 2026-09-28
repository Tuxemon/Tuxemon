# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.database.runtime import db
from tuxemon.db import TechCategory, TechniqueModel
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


@dataclass
class LearnMmEffect(CoreEffect):
    """
    Applies the "learn_mm" effect to a monster.

    This effect teaches the target a random technique of the specified
    element type. Techniques are chosen from the database, excluding
    reserved categories and moves the monster already knows.

    **Parameters**

    - ``element``: The elemental type of the technique to learn
      (e.g., ``wood``, ``water``, ``fire``).

    **Example**

    .. code-block:: json

        "effects": [
            "learn_mm water"
        ]
    """

    name = "learn_mm"
    element: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        TechniqueModel.load_cache(db)
        cache = TechniqueModel.get_cache()

        # Filter AFTER cache load
        filtered = {
            slug: tech
            for slug, tech in cache.items()
            if tech.category != TechCategory.reserved
            and self.element in tech.types
        }

        known_moves = [tech.slug for tech in target.moves.get_moves()]
        available = list(set(filtered.keys()) - set(known_moves))

        if available:
            tech_slug = random.choice(available)

            if target.moves.has_move(tech_slug):
                return ItemEffectResult(name=item.name)

            tech = Technique.create(tech_slug)
            learned = target.moves.learn(target, tech, ignore_eligibility=True)
            if not learned:
                return ItemEffectResult(name=item.name)

            return ItemEffectResult(name=item.name, success=True)

        return ItemEffectResult(name=item.name)
