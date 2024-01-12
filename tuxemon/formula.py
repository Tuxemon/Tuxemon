# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import datetime as dt
import logging
import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tuxemon import prepare as pre

if TYPE_CHECKING:
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

    m = min(pre.MAX_MULTIPLIER, m)
    m = max(pre.MIN_MULTIPLIER, m)
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
        user_strength = user.melee * (pre.COEFF_DAMAGE + user.level)
        target_resist = target.armour
    elif technique.range == "touch":
        user_strength = user.melee * (pre.COEFF_DAMAGE + user.level)
        target_resist = target.dodge
    elif technique.range == "ranged":
        user_strength = user.ranged * (pre.COEFF_DAMAGE + user.level)
        target_resist = target.dodge
    elif technique.range == "reach":
        user_strength = user.ranged * (pre.COEFF_DAMAGE + user.level)
        target_resist = target.armour
    elif technique.range == "reliable":
        user_strength = pre.COEFF_DAMAGE + user.level
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


def simple_recover(target: Monster, divisor: int) -> int:
    """
    Simple recover based on target's full hp.

    Parameters:
        target: The one being healed.
        divisor: The number by which target HP is to be divided.

    Returns:
        Recovered health.

    """
    heal = min(target.hp // divisor, target.hp - target.current_hp)
    return heal


def simple_lifeleech(user: Monster, target: Monster, divisor: int) -> int:
    """
    Simple lifeleech based on a few factors.

    Parameters:
        user: The monster getting HPs.
        target: The monster losing HPs.
        divisor: The number by which target HP is to be divided.

    Returns:
        Damage/Gain of HPs.

    """
    heal = min(
        target.hp // divisor, target.current_hp, user.hp - user.current_hp
    )
    return heal


def update_armour(mon: Monster) -> int:
    """
    It returns a bonus / malus of the stat based on additional parameters.
    """
    # tastes - which gives the bonus and which the malus
    _malus, _bonus = pre.TASTE_RANGE
    malus = mon.armour * _malus if mon.taste_cold == "soft" else 0.0
    bonus = mon.armour * _bonus if mon.taste_warm == "hearty" else 0.0
    return int(bonus + malus)


def update_speed(mon: Monster) -> int:
    """
    It returns a bonus / malus of the stat based on additional parameters.
    """
    # tastes - which gives the bonus and which the malus
    _malus, _bonus = pre.TASTE_RANGE
    malus = mon.speed * _malus if mon.taste_cold == "mild" else 0.0
    bonus = mon.speed * _bonus if mon.taste_warm == "peppy" else 0.0
    return int(bonus + malus)


def update_melee(mon: Monster) -> int:
    """
    It returns a bonus / malus of the stat based on additional parameters.
    """
    # tastes - which gives the bonus and which the malus
    _malus, _bonus = pre.TASTE_RANGE
    malus = mon.melee * _malus if mon.taste_cold == "sweet" else 0.0
    bonus = mon.melee * _bonus if mon.taste_warm == "salty" else 0.0
    return int(bonus + malus)


def update_ranged(mon: Monster) -> int:
    """
    It returns a bonus / malus of the stat based on additional parameters.
    """
    # tastes - which gives the bonus and which the malus
    _malus, _bonus = pre.TASTE_RANGE
    malus = mon.ranged * _malus if mon.taste_cold == "flakey" else 0.0
    bonus = mon.ranged * _bonus if mon.taste_warm == "zesty" else 0.0
    return int(bonus + malus)


def update_dodge(mon: Monster) -> int:
    """
    It returns a bonus / malus of the stat based on additional parameters.
    """
    # tastes - which gives the bonus and which the malus
    _malus, _bonus = pre.TASTE_RANGE
    malus = mon.dodge * _malus if mon.taste_cold == "dry" else 0.0
    bonus = mon.dodge * _bonus if mon.taste_warm == "refined" else 0.0
    return int(bonus + malus)


def today_ordinal() -> int:
    """
    It gives today's proleptic Gregorian ordinal.
    """
    return dt.date.today().toordinal()


def set_weight(kg: float) -> float:
    """
    It generates a personalized weight,
    random number: between +/- 10%.
    Eg 100 kg +/- 10 kg
    """
    _minor, _major = pre.WEIGHT_RANGE
    if kg == 0:
        weight = kg
    else:
        minor = kg + (kg * _minor)
        major = kg + (kg * _major)
        weight = round(random.uniform(minor, major), 2)
    return weight


def set_height(cm: float) -> float:
    """
    It generates a personalized height,
    random number: between +/- 10%.
    Eg 100 cm +/- 10 cm
    """
    _minor, _major = pre.HEIGHT_RANGE
    if cm == 0:
        height = cm
    else:
        minor = cm + (cm * _minor)
        major = cm + (cm * _major)
        height = round(random.uniform(minor, major), 2)
    return height


def convert_lbs(kg: float) -> float:
    """
    It converts kilograms into pounds.
    """
    return round(kg * pre.COEFF_POUNDS, 2)


def convert_ft(cm: float) -> float:
    """
    It converts centimeters into feet.
    """
    return round(cm * pre.COEFF_FEET, 2)


def convert_km(steps: float) -> float:
    """
    It converts steps into kilometers.
    """
    return round(steps / 1000, 2)


def convert_mi(steps: float) -> float:
    """
    It converts steps into miles.
    """
    km = convert_km(steps)
    return round(km * pre.COEFF_MILES, 2)


def diff_percentage(part: float, total: float, decimal: int = 1) -> float:
    """
    It returns the difference between two numbers in percentage format.

    Parameters:
        part: The part, number.
        total: The total, number.
        decimal: How many decimals, default 1.

    Returns:
        The difference in percentage.

    """
    return round(((part - total) / total) * 100, decimal)


def shake_check(
    target: Monster, status_modifier: float, tuxeball_modifier: float
) -> float:
    """
    It calculates the shake_check.

    Parameters:
        target: The monster we are trying to catch.
        status_modifier: The status modifier.
        tuxeball_modifier: The tuxeball modifier.

    Returns:
        The shake check.
    """
    # The max catch rate.
    max_catch_rate = pre.MAX_CATCH_RATE
    # Constant used in shake_check calculations
    shake_constant = pre.SHAKE_CONSTANT

    # This is taken from http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
    # Specifically the catch rate and the shake_check is based on the Generation III-IV
    # The rate of which a tuxemon is caught is approximately catch_check/255
    catch_check = (
        (3 * target.hp - 2 * target.current_hp)
        * target.catch_rate
        * status_modifier
        * tuxeball_modifier
        / (3 * target.hp)
    )
    shake_check = shake_constant / (
        math.sqrt(math.sqrt(max_catch_rate / catch_check)) * 8
    )
    # Catch_resistance is a randomly generated number between the lower and upper catch_resistance of a tuxemon.
    # This value is used to slightly increase or decrease the chance of a tuxemon being caught. The value changes
    # Every time a new capture device is thrown.
    catch_resistance = random.uniform(
        target.lower_catch_resistance, target.upper_catch_resistance
    )
    # Catch_resistance is applied to the shake_check
    shake_check = shake_check * catch_resistance

    # Debug section
    logger.debug("--- Capture Variables ---")
    logger.debug(
        "(3*target.hp - 2*target.current_hp) "
        "* target.catch_rate * status_modifier * tuxeball_modifier / (3*target.hp)"
    )

    msg = "(3 * {0.hp} - 2 * {0.current_hp}) * {0.catch_rate} * {1} * {2} / (3 * {0.hp})"

    logger.debug(msg.format(target, status_modifier, tuxeball_modifier))
    logger.debug("shake_constant/(sqrt(sqrt(max_catch_rate/catch_check))*8)")
    logger.debug(f"524325/(sqrt(sqrt(255/{catch_check}))*8)")

    msg = "Each shake has a {}/65536 chance of breaking the creature free. (shake_check = {})"
    logger.debug(
        msg.format(
            round((shake_constant - shake_check) / shake_constant, 2),
            round(shake_check),
        )
    )
    return shake_check


def capture(shake_check: float) -> tuple[bool, int]:
    """
    It defines if the wild monster is captured or not.

    Parameters:
        shake_check: Float.

    Returns:
        If it's captured: (True, total_shakes)
        If it isn't captured: (False, nr_shakes)

    """
    # The number of shakes that a tuxemon can do to escape.
    total_shakes = pre.TOTAL_SHAKES
    # In every shake a random number form [0-65536] will be produced.
    max_shake_rate = pre.MAX_SHAKE_RATE
    # 4 shakes to give monster chance to escape
    for i in range(0, total_shakes):
        random_num = random.randint(0, max_shake_rate)
        logger.debug(f"shake check {i}: random number {random_num}")
        if random_num > int(shake_check):
            return (False, i + 1)
    return (True, total_shakes)
