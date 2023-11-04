# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
import logging
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.db import MonsterModel
    from tuxemon.element import Element
    from tuxemon.monster import Monster
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


def simple_damage_multiplier(
    attack_types: Sequence[Element],
    target_types: Sequence[Element],
) -> float:
    """
    Calculates damage multiplier based on strengths and weaknesses.

    Parameters:
        attack_types: The types of the technique.
        target_types: The types of the target.

    Returns:
        The attack multiplier.

    """
    m = 1.0
    for attack_type in attack_types:
        for target_type in target_types:
            if target_type:
                if (
                    attack_type.slug == "aether"
                    or target_type.slug == "aether"
                ):
                    continue
                m = attack_type.lookup_multiplier(target_type.slug)

    m = min(4, m)
    m = max(0.25, m)
    return m


def simple_damage_calculate(
    technique: Technique,
    user: Monster,
    target: Monster,
) -> tuple[int, float]:
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
    else:
        raise RuntimeError(
            "unhandled damage category %s",
            technique.range,
        )

    mult = simple_damage_multiplier(
        (technique.types),
        (target.types),
    )
    move_strength = technique.power * mult
    damage = int(user_strength * move_strength / target_resist)
    return damage, mult


def damage_full_hp(target: Monster, value: int) -> int:
    """
    Damage based on target's full hp.

    Parameters:
        target: The one the technique is being used on.
        value: Numerical value (target.hp // value).

    Returns:
        Inflicted damage.

    """
    damage = target.hp // value
    return damage


def simple_recover(target: Monster) -> int:
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


def simple_lifeleech(user: Monster, target: Monster) -> int:
    """
    Simple lifeleech based on a few factors.

    Parameters:
        technique: The technique causing lifeleech.
        user: The user of the technique.
        target: The one the technique is being used on.

    Returns:
        Inflicted damage.

    """
    if user.current_hp <= 0:
        damage = 0
    else:
        damage = min(
            target.hp // 16, target.current_hp, user.hp - user.current_hp
        )
    return damage


def simple_grabbed(monster: Monster) -> None:
    for move in monster.moves:
        if move.range.ranged:
            move.potency = move.default_potency * 0.5
            move.power = move.default_power * 0.5
        elif move.range.reach:
            move.potency = move.default_potency * 0.5
            move.power = move.default_power * 0.5


def simple_stuck(monster: Monster) -> None:
    for move in monster.moves:
        if move.range.melee:
            move.potency = move.default_potency * 0.5
            move.power = move.default_power * 0.5
        elif move.range.touch:
            move.potency = move.default_potency * 0.5
            move.power = move.default_power * 0.5


def check_taste(monster: Monster, stat: str) -> int:
    """
    It checks the taste and return the value
    """
    positive = 0
    negative = 0
    if stat == "speed":
        if monster.taste_cold == "mild":
            negative = (monster.speed) * 10 // 100
        if monster.taste_warm == "peppy":
            positive = (monster.speed) * 10 // 100
        value = positive - negative
        return value
    elif stat == "melee":
        if monster.taste_cold == "sweet":
            negative = (monster.melee) * 10 // 100
        if monster.taste_warm == "salty":
            positive = (monster.melee) * 10 // 100
        value = positive - negative
        return value
    elif stat == "armour":
        if monster.taste_cold == "soft":
            negative = (monster.armour) * 10 // 100
        if monster.taste_warm == "hearty":
            positive = (monster.armour) * 10 // 100
        value = positive - negative
        return value
    elif stat == "ranged":
        if monster.taste_cold == "flakey":
            negative = (monster.ranged) * 10 // 100
        if monster.taste_warm == "zesty":
            positive = (monster.ranged) * 10 // 100
        value = positive - negative
        return value
    elif stat == "dodge":
        if monster.taste_cold == "dry":
            negative = (monster.dodge) * 10 // 100
        if monster.taste_warm == "refined":
            positive = (monster.dodge) * 10 // 100
        value = positive - negative
        return value
    else:
        value = positive
        return value


def today_ordinal() -> int:
    """
    It gives today's proleptic Gregorian ordinal.
    """
    today = dt.date.today().toordinal()
    return today


def set_weight(kg: float) -> float:
    """
    It generates a personalized weight,
    random number: between +/- 10%.
    Eg 100 kg +/- 10 kg
    """
    if kg == 0:
        weight = kg
    else:
        minor = kg - (kg * 0.1)
        major = (kg * 0.1) + kg
        weight = round(random.uniform(minor, major), 2)
    return weight


def set_height(cm: float) -> float:
    """
    It generates a personalized height,
    random number: between +/- 10%.
    Eg 100 cm +/- 10 cm
    """
    if cm == 0:
        height = cm
    else:
        minor = cm - (cm * 0.1)
        major = (cm * 0.1) + cm
        height = round(random.uniform(minor, major), 2)
    return height


def convert_lbs(kg: float) -> float:
    """
    It converts kilograms into pounds.
    """
    pounds = round(kg * 2.2046, 2)
    return pounds


def convert_ft(cm: float) -> float:
    """
    It converts centimeters into feet.
    """
    foot = round(cm * 0.032808399, 2)
    return foot


def convert_km(steps: float) -> float:
    """
    It converts steps into kilometers.
    One tile: 1 meter
    """
    m = steps * 1
    km = round(m / 1000, 2)
    return km


def convert_mi(steps: float) -> float:
    """
    It converts steps into miles.
    """
    km = convert_km(steps)
    mi = round(km * 0.6213711922, 2)
    return mi


def weight_height_diff(
    monster: Monster, db: MonsterModel
) -> tuple[float, float]:
    weight = round(((monster.weight - db.weight) / db.weight) * 100, 1)
    height = round(((monster.height - db.height) / db.height) * 100, 1)
    return weight, height
