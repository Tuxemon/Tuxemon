# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster

if TYPE_CHECKING:
    from tuxemon.item.item import Item


@dataclass
class EvolveEffect(ItemEffect):
    """This effect evolves the target into the monster in the parameters."""

    name = "evolve"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> ItemEffectResult:
        assert target and target.owner
        if not target.evolutions:
            return ItemEffectResult(
                name=item.name, success=False, num_shakes=0, extras=[]
            )
        choices = [d for d in target.evolutions if d.item == item.slug]
        if len(choices) == 1:
            evolution = choices[0].monster_slug
        else:
            evolution = random.choice(choices).monster_slug

        new_monster = Monster()
        new_monster.load_from_db(evolution)
        target.evolution_handler.evolve_monster(new_monster)

        self.session.client.push_state(
            "EvolutionTransition",
            original=target.slug,
            evolved=new_monster.slug,
        )
        return ItemEffectResult(
            name=item.name, success=True, num_shakes=0, extras=[]
        )
