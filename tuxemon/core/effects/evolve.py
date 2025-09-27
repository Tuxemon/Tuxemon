# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.db import MonsterEvolutionItemModel
from tuxemon.monster import Monster

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


@dataclass
class EvolveEffect(CoreEffect):
    """This effect evolves the target into the monster in the parameters."""

    name = "evolve"

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        if not target.evolutions:
            return ItemEffectResult(name=item.name)

        possible_evolutions: list[tuple[MonsterEvolutionItemModel, float]] = []
        for evolution_model in target.evolutions:
            item_weights = evolution_model.item
            if isinstance(item_weights, dict) and item.slug in item_weights:
                weight = item_weights[item.slug]
                if weight > 0.0:
                    possible_evolutions.append((evolution_model, weight))

        if not possible_evolutions:
            return ItemEffectResult(name=item.name)

        if len(possible_evolutions) == 1:
            selected_evolution_model = possible_evolutions[0][0]
        else:
            evolution_choices, weights = zip(*possible_evolutions)
            selected_evolution_model = random.choices(
                evolution_choices, weights=weights, k=1
            )[0]

        evolution_slug = selected_evolution_model.monster_slug
        new_monster = Monster.create(evolution_slug)
        target.evolution_handler.evolve_monster(new_monster)

        session.client.push_state(
            "EvolutionTransition",
            original=target.slug,
            evolved=new_monster.slug,
        )

        return ItemEffectResult(name=item.name, success=True)
