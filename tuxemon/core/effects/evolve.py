# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
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

        context = {"use_item": True}
        possible_evolutions = (
            target.evolution_handler.get_possible_item_evolutions(
                item, context
            )
        )

        if not possible_evolutions:
            return ItemEffectResult(name=item.name)

        selected_evolution_model = (
            target.evolution_handler.choose_evolution_model(
                possible_evolutions
            )
        )
        new_monster = Monster.create(selected_evolution_model.monster_slug)
        target.evolution_handler.evolve_monster(new_monster)

        session.client.push_state(
            "EvolutionTransition",
            original=target.slug,
            evolved=new_monster.slug,
        )

        return ItemEffectResult(name=item.name, success=True)
