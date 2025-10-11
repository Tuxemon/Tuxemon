# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.formula import config_monster

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class FoodPreferenceEffect(CoreEffect):
    """Attempts to capture the target."""

    name = "food_preference"
    warm: str
    cold: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        self.session = session
        bond_delta = get_bond_from_food(
            target, self.warm.lower(), self.cold.lower()
        )
        target.bond_handler.change_bond(bond_delta)
        return ItemEffectResult(name=item.name, success=True)


def is_opposite_taste(taste_a: str, taste_b: str) -> bool:
    """Checks if two tastes are opposites, regardless of direction."""
    opposites = config_monster.opposite_tastes
    return taste_b in opposites.get(taste_a, []) or taste_a in opposites.get(
        taste_b, []
    )


def get_bond_from_food(
    monster: Monster, warm_taste: str, cold_taste: str
) -> int:
    """
    Calculates the bond adjustment based on taste alignment.
    """
    warm_match = warm_taste == monster.taste_warm
    cold_match = cold_taste == monster.taste_cold

    warm_opposite = is_opposite_taste(warm_taste, monster.taste_warm)
    cold_opposite = is_opposite_taste(cold_taste, monster.taste_cold)

    bond_preferences = config_monster.bond_preferences

    if warm_match and cold_match:
        return bond_preferences.get("great", 0)
    elif warm_match or cold_match:
        return bond_preferences.get("good", 0)
    elif warm_opposite and cold_opposite:
        return bond_preferences.get("terrible", 0)
    elif warm_opposite or cold_opposite:
        return bond_preferences.get("bad", 0)
    else:
        return bond_preferences.get("average", 0)
