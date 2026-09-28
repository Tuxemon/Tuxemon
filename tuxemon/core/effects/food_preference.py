# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import CoreEffect, ItemEffectResult
from tuxemon.database.rules import config_monster
from tuxemon.taste import Taste

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

TASTE_PREFIX = "taste_"


@dataclass
class FoodPreferenceEffect(CoreEffect):
    """
    Applies a bond change based on the target monster's food preferences.

    This effect compares the provided warm and cold tastes against the monster's
    own tastes. Matching preferences increase bond, opposite tastes decrease it,
    and neutral combinations apply an average change. Opposites are determined
    using the configured taste map.

    Tastes are identified by slug (``salty``, ``sweet``, ...). The ``taste_``
    prefixed form used by translation msgids is accepted as well.

    **Parameters**

    - ``warm``: The warm taste to compare (string).
    - ``cold``: The cold taste to compare (string).

    **Example**

    .. code-block:: json

        "effects": [
            "food_preference salty sweet"
        ]
    """

    name = "food_preference"
    warm: str
    cold: str

    def apply_item_target(
        self, session: Session, item: Item, target: Monster
    ) -> ItemEffectResult:
        self.session = session
        bond_delta = get_bond_from_food(target, self.warm, self.cold)
        floor = target.bond_handler.get_effective_min_bond(target.stage)
        crossed = target.bond_handler.change_bond(bond_delta, floor)
        if crossed:
            logger.debug(f"{target.name} crossed bond milestones: {crossed}")
        return ItemEffectResult(name=item.name, success=True)


def normalize_taste(taste: str) -> str:
    """
    Reduces a taste identifier to its canonical slug.

    Monsters store tastes as slugs (``salty``), while translation msgids and
    some data files use the ``taste_`` prefixed form (``taste_salty``). Both
    are accepted so item definitions written either way keep working.
    """
    taste = taste.lower()
    return (
        taste[len(TASTE_PREFIX) :] if taste.startswith(TASTE_PREFIX) else taste
    )


def is_opposite_taste(taste_a: str, taste_b: str) -> bool:
    """Checks if two tastes are opposites, regardless of direction."""
    taste_a = normalize_taste(taste_a)
    taste_b = normalize_taste(taste_b)
    opposites = {
        normalize_taste(key): [normalize_taste(value) for value in values]
        for key, values in config_monster.opposite_tastes.items()
    }
    return taste_b in opposites.get(taste_a, []) or taste_a in opposites.get(
        taste_b, []
    )


def get_bond_from_food(
    monster: Monster, warm_taste: str, cold_taste: str
) -> int:
    """
    Calculates the bond adjustment based on taste alignment.
    """
    warm_taste = normalize_taste(warm_taste)
    cold_taste = normalize_taste(cold_taste)
    monster_warm = normalize_taste(monster.taste_warm)
    monster_cold = normalize_taste(monster.taste_cold)

    known_tastes = Taste.get_all_tastes()
    for taste, taste_type in ((warm_taste, "warm"), (cold_taste, "cold")):
        known = known_tastes.get(taste)
        if known is None or known.taste_type != taste_type:
            logger.warning(
                f"'{taste}' isn't a known {taste_type} taste, it will never match."
            )

    warm_match = warm_taste == monster_warm
    cold_match = cold_taste == monster_cold
    # Opposite pairs always span the two taste types (e.g. salty/sweet), so a
    # dish's warm taste is weighed against the monster's cold preference and
    # its cold taste against the monster's warm preference.
    warm_opposite = is_opposite_taste(warm_taste, monster_cold)
    cold_opposite = is_opposite_taste(cold_taste, monster_warm)
    bond_preferences = config_monster.bond_preferences

    if warm_match and cold_match:
        key = "great"
    elif warm_match or cold_match:
        key = "good"
    elif warm_opposite and cold_opposite:
        key = "terrible"
    elif warm_opposite or cold_opposite:
        key = "bad"
    else:
        key = "average"

    if key not in bond_preferences:
        logger.warning(f"Bond preference key '{key}' not found in config.")
    return bond_preferences.get(key, 0)
