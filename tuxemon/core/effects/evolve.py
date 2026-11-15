# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.session import Session


@dataclass
class EvolveEffect(CoreEffect):
    """
    Evolves the target monster into a new form based on item parameters.

    This effect checks the target's available evolutions and determines whether
    the triggering item can cause an evolution. If multiple valid evolutions
    exist, one is selected randomly according to weighted probabilities.

    **Example**

    .. code-block:: json

        "effects": [
            "evolve"
        ]
    """

    name = "evolve"

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        context = {"use_item": True}
        possible = target.evolution_handler.get_possible_item_evolutions(
            item, context
        )
        if not possible:
            return ItemEffectResult(name=item.name, success=False)

        model = target.evolution_handler.choose_evolution_model(possible)
        registry = target.get_owner().evolution_registry
        registry.add_pending(target.instance_id, model.monster_slug)

        target.waiting_to_evolve = True
        return ItemEffectResult(name=item.name, success=True)
