# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    value: Union[str, None]

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> EvolveEffectResult:
        assert target
        if self.value:
            if self.value == "random":
                choices = [d for d in target.evolutions if d.path == "item"]
                evolution = random.choice(choices).monster_slug
                self.user.evolve_monster(target, evolution)
                return {"success": True}
        else:
            choices = [d for d in target.evolutions if d.item == item.slug]
            if len(choices) == 1:
                self.user.evolve_monster(target, choices[0].monster_slug)
                return {"success": True}
            elif len(choices) > 1:
                evolution = random.choice(choices).monster_slug
                self.user.evolve_monster(target, evolution)
                return {"success": True}
        return {"success": False}
