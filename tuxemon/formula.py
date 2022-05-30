#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Yisroel Newmark <ymnewmark@gmail.com>
#
#
#
#

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.technique import Technique

logger = logging.getLogger(__name__)


class TypeChart(NamedTuple):
    strong_attack: Optional[str]
    weak_attack: Optional[str]
    extra_damage: Optional[str]
    resist_damage: Optional[str]


TYPES = {
    "aether": TypeChart(None, None, None, None),
    "normal": TypeChart(None, None, None, None),
    "wood": TypeChart("earth", "fire", "metal", "water"),
    "fire": TypeChart("metal", "earth", "water", "wood"),
    "earth": TypeChart("water", "metal", "wood", "fire"),
    "metal": TypeChart("wood", "water", "fire", "earth"),
    "water": TypeChart("fire", "wood", "earth", "metal"),
}


def simple_damage_multiplier(
    attack_types: Sequence[Optional[str]],
    target_types: Sequence[str],
) -> float:
    """
    Calculates damage multiplier based on strengths and weaknesses.

    Parameters:
        attack_types: The names of the types of the technique.
        target_types: The names of the types of the target.

    Returns:
        The attack multiplier.

    """
    m = 1.0
    for attack_type in attack_types:
        if attack_type is None:
            continue

        for target_type in target_types:
            body = TYPES.get(target_type, TYPES["aether"])
            if body.extra_damage is None:
                continue
            if attack_type == body.extra_damage:
                m *= 2
            elif attack_type == body.resist_damage:
                m /= 2.0
    m = min(4, m)
    m = max(0.25, m)
    return m


def simple_damage_calculate(
    technique: Technique,
    user: Monster,
    target: Monster,
) -> Tuple[int, float]:
    """
    Calculates the damage of a technique based on stats and multiplier.

    Parameters:
        technique: The technique to calculate for.
        user: The user of the technique.
        target: The one the technique is being used on.

    Returns:
        A tuple (damage, multiplier).

    """
    if technique.range == "melee":
        user_strength = user.melee * (7 + user.level)
        target_resist = target.armour
    elif technique.range == "touch":
        user_strength = user.melee * (7 + user.level)
        target_resist = target.dodge
    elif technique.range == "ranged":
        user_strength = user.ranged * (7 + user.level)
        target_resist = target.dodge
    elif technique.range == "reach":
        user_strength = user.ranged * (7 + user.level)
        target_resist = target.armour
    elif technique.range == "reliable":
        user_strength = 7 + user.level
        target_resist = 1
    elif technique.range == "special":
        logger.warning(
            f"Tried to use {technique.name} with damage effect, but has range 'special'"
        )
        return 0, 0
    else:
        logger.error(
            "unhandled damage category %s %s",
            technique.category,
            technique.range,
        )
        raise RuntimeError

    mult = simple_damage_multiplier(
        (technique.type1, technique.type2), (target.type1, target.type2)
    )
    move_strength = technique.power * mult
    damage = int(user_strength * move_strength / target_resist)
    return damage, mult


def simple_poison(
    technique: Technique,
    user: Monster,
    target: Monster,
) -> int:
    """
    Simple poison based on target's full hp.

    Parameters:
        technique: The technique causing poison.
        user: The user of the technique.
        target: The one the technique is being used on.

    Returns:
        Inflicted damage.

    """
    damage = target.hp // 8
    return damage


def simple_recover(
    technique: Technique,
    target: Monster,
) -> int:
    """
    Simple recover based on target's full hp.

    Parameters:
        technique: The technique causing recover.
        target: The one being healed.

    Returns:
        Recovered health.

    """
    heal = min(target.hp // 16, target.hp - target.current_hp)
    return heal


def simple_lifeleech(
    technique: Technique,
    user: Monster,
    target: Monster,
) -> int:
    """
    Simple lifeleech based on a few factors.

    Parameters:
        technique: The technique causing lifeleech.
        user: The user of the technique.
        target: The one the technique is being used on.

    Returns:
        Inflicted damage.

    """
    damage = min(target.hp // 2, target.current_hp, user.hp - user.current_hp)
    return damage


def simple_overfeed(
    technique: Technique,
    user: Monster,
    target: Monster,
) -> int:
    speed = target.speed // 2
    return speed
