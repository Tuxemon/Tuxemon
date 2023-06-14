# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Union

from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class VariableEffectResult(ItemEffectResult):
    pass


@dataclass
class VariableEffect(ItemEffect):
    """
    Creates a game variable, format xx:yy.
    If the value "yy" is "step", then the game
    variable will be xx_steps:yy where yy are
    the exact number of the player's step.

    variable key:value
    variable key:steps > key_steps:nr_steps

    """

    name = "variable"
    optional: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> VariableEffectResult:
        player = self.session.player
        ret: bool = False
        elements: List[str] = []
        if self.optional.find(":"):
            elements = self.optional.split(":")
        if elements:
            if elements[1] == "steps":
                player.game_variables[
                    f"{elements[0]}_steps"
                ] = player.game_variables["steps"]
                ret = True
            else:
                player.game_variables[elements[0]] = elements[1]
                ret = True

        return {"success": ret}
