# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.db import ElementType
from tuxemon.item.item import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class SwitchEffectResult(ItemEffectResult):
    pass


@dataclass
class SwitchEffect(ItemEffect):
    """
    Changes monster type.
    "switch wood"
    "switch fire"
    "switch random"
    if "switch random"
    then the type is chosen randomly.

    """

    name = "switch"
    element: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> SwitchEffectResult:
        done: bool = False
        elements = list(ElementType)
        if self.element in elements:
            ele = ElementType(self.element)
            if ele not in target.types:
                target.types = [ele]
                done = True
        if self.element == "random":
            _target = random.choice(elements)
            target.types = [_target]
            done = True
        return {"success": done}
