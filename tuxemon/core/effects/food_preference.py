# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.formula import change_bond

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

OPPOSITE_TASTES = {
    "taste_peppy": "taste_mild",
    "taste_mild": "taste_peppy",
    "taste_salty": "taste_sweet",
    "taste_sweet": "taste_salty",
    "taste_hearty": "taste_soft",
    "taste_soft": "taste_hearty",
    "taste_zesty": "taste_flakey",
    "taste_flakey": "taste_zesty",
    "taste_refined": "taste_dry",
    "taste_dry": "taste_refined",
    "taste_savory": "taste_bland",
    "taste_bland": "taste_savory",
}


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
        preference = get_food_preference(
            target, self.warm.lower(), self.cold.lower()
        )
        bond_delta = bond_from_food_preference(preference)
        change_bond(target, bond_delta)
        return ItemEffectResult(name=item.name, success=True)


def is_opposite_taste(taste_a: str, taste_b: str) -> bool:
    return OPPOSITE_TASTES.get(taste_a) == taste_b


def get_food_preference(
    monster: Monster, warm_taste: str, cold_taste: str
) -> str:
    """
    Returns preference level based on taste alignment.
    """
    warm_match = warm_taste == monster.taste_warm
    cold_match = cold_taste == monster.taste_cold

    warm_opposite = is_opposite_taste(warm_taste, monster.taste_warm)
    cold_opposite = is_opposite_taste(cold_taste, monster.taste_cold)

    if warm_match and cold_match:
        return "Great"
    elif warm_match or cold_match:
        return "Good"
    elif warm_opposite and cold_opposite:
        return "Terrible"
    elif warm_opposite or cold_opposite:
        return "Bad"
    else:
        return "Average"


def bond_from_food_preference(preference: str) -> int:
    """Maps preference level to bond (happiness) adjustment."""
    return {
        "Great": +10,
        "Good": +5,
        "Average": 0,
        "Bad": -5,
        "Terrible": -10,
    }.get(preference, 0)
