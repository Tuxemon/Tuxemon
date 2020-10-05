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

import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

type_chart = namedtuple(
    "TypeChart", ["strong_attack", "weak_attack", "extra_damage", "resist_damage"]
)
TYPES = {
    "aether": type_chart(None, None, None, None),
    "normal": type_chart(None, None, None, None),
    "wood": type_chart("earth", "fire", "metal", "water"),
    "fire": type_chart("metal", "earth", "water", "wood"),
    "earth": type_chart("water", "metal", "wood", "fire"),
    "metal": type_chart("wood", "water", "fire", "earth"),
    "water": type_chart("fire", "wood", "earth", "metal"),
}


def simple_damage_multiplier(attack_types, target_types):
    """ Calculates damage multiplier based on strengths and weaknesses

    :param attack_types: The names of the types of the technique.
    :param target_types: The names of the types of the target.

    :type attack_types: list
    :type attack_types: list

    :rtype: number
    :returns: the attack multiplier
    """
    m = 1
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


def simple_damage_calculate(technique, user, target):
    """ Calculates the damage of a technique based on stats and multiplier.

    :param technique: The technique to calculate for.
    :param user: The user of the technique.
    :param target: The one the technique is being used on.

    :type technique: tuxemon.core.technique.Technique
    :type user: tuxemon.core.monster.Monster
    :type target: tuxemon.core.monster.Monster

    :return: damage, multiplier
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
    else:
        logger.error(
            "unhandled damage category %s %s", technique.category, technique.range
        )
        raise RuntimeError

    mult = simple_damage_multiplier(
        (technique.type1, technique.type2), (target.type1, target.type2)
    )
    move_strength = technique.power * mult
    damage = int(user_strength * move_strength / target_resist)
    return damage, mult


def simple_poison(technique, user, target):
    """ Simple poison based on target's full hp.

    :param technique: The technique causing poison.
    :param user: The user of the technique.
    :param target: The one the technique is being used on.

    :type technique: tuxemon.core.technique.Technique
    :type user: tuxemon.core.monster.Monster
    :type target: tuxemon.core.monster.Monster

    :return: damage
    """
    damage = target.hp / 8
    return damage


def simple_recover(technique, target):
    """ Simple recover based on target's full hp.

    :param technique: The technique causing recover.
    :param target: The one being healed.

    :type technique: tuxemon.core.technique.Technique
    :type target: tuxemon.core.monster.Monster

    :return: heal
    """
    heal = min(target.hp / 16, target.hp - target.current_hp)
    return heal


def simple_lifeleech(technique, user, target):
    """ Simple lifeleech based on a few factors.

    :param technique: The technique causing lifeleech.
    :param user: The user of the technique.
    :param target: The one the technique is being used on.

    :type technique: tuxemon.core.technique.Technique
    :type user: tuxemon.core.monster.Monster
    :type target: tuxemon.core.monster.Monster

    :return: damage
    """
    damage = min(target.hp / 2, target.current_hp, user.hp - user.current_hp)
    return damage
