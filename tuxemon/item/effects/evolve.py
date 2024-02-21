# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class EvolveEffectResult(ItemEffectResult):
    pass


@dataclass
class EvolveEffect(ItemEffect):
    """This effect evolves the target into the monster in the parameters."""

    name = "evolve"

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> EvolveEffectResult:
        assert target and target.owner
        evolve: bool = False
        choices = [d for d in target.evolutions if d.item == item.slug]
        if len(choices) == 1:
            evolution = choices[0].monster_slug
            evolve = True
        else:
            evolution = random.choice(choices).monster_slug
            evolve = True
        if evolve and evolution:
            target.owner.evolve_monster(target, evolution)
        return {"success": evolve, "num_shakes": 0, "extra": None}
