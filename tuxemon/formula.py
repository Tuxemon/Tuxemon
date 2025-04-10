# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import yaml

from tuxemon import prepare as pre
from tuxemon.constants import paths

if TYPE_CHECKING:
    from tuxemon.db import Modifier
    from tuxemon.element import Element
    from tuxemon.monster import Monster
    from tuxemon.taste import Taste
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)

multiplier_cache: dict[tuple[str, str], float] = {}


@dataclass
class StatWeight:
    stat: str
    weight: float


@dataclass
class RangeMapEntry:
    user_stat: StatWeight
    target_stat: StatWeight


@dataclass
class CaptureConfig:
    total_shakes: int
    shake_constant: int
    shake_denominator: int
    shake_divisor: int
    shake_hp_multiplier: int
    shake_current_hp_multiplier: int
    shake_hp_divisor: int


def load_yaml(filepath: str) -> Any:
    try:
        with open(filepath) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


class Loader:
    _config_capture: Optional[CaptureConfig] = None
    _range_map: dict[str, RangeMapEntry] = {}

    @classmethod
    def get_config_capture(cls, filename: str) -> CaptureConfig:
        yaml_path = f"{paths.mods_folder}/{filename}"
        if cls._config_capture is None:
            raw_map = load_yaml(yaml_path)
            cls._config_capture = CaptureConfig(**raw_map)
        return cls._config_capture

    @classmethod
    def get_range_map(cls, filename: str) -> dict[str, RangeMapEntry]:
        yaml_path = f"{paths.mods_folder}/{filename}"
        if not cls._range_map:
            raw_map = load_yaml(yaml_path)
            cls._range_map = {
                key: RangeMapEntry(
                    user_stat=StatWeight(
                        stat=item[0]["user_stat"], weight=item[0]["weight"]
                    ),
                    target_stat=StatWeight(
                        stat=item[1]["target_stat"], weight=item[1]["weight"]
                    ),
                )
                for key, item in raw_map.items()
            }
        return cls._range_map


def simple_damage_multiplier(
    attack_types: Sequence[Element],
    target_types: Sequence[Element],
    additional_factors: Optional[dict[str, float]] = None,
) -> float:
    """
    Calculates damage multiplier based on strengths and weaknesses.

    Parameters:
        attack_types: The types of the technique.
        target_types: The types of the target.
        additional_factors: A dictionary of additional factors to apply to
        the damage multiplier (default None)

    Returns:
        The attack multiplier.
    """
    multiplier = 1.0
    for attack_type in attack_types:
        for target_type in target_types:
            if target_type and not (
                attack_type.slug == "aether" or target_type.slug == "aether"
            ):
                key = (attack_type.slug, target_type.slug)
                if key in multiplier_cache:
                    multiplier = multiplier_cache[key]
                else:
                    multiplier = attack_type.lookup_multiplier(
                        target_type.slug
                    )
                    multiplier_cache[key] = multiplier
                multiplier = min(
                    pre.MULTIPLIER_RANGE[1],
                    max(pre.MULTIPLIER_RANGE[0], multiplier),
                )
    # Apply additional factors
    if additional_factors:
        factor_multiplier = math.prod(additional_factors.values())
        multiplier *= factor_multiplier
    return multiplier


def calculate_multiplier(
    monster_types: Sequence[Element], opponent_types: Sequence[Element]
) -> float:
    """
    Calculate the multiplier for a monster's types against an opponent's types.

    Parameters:
        monster (Monster): The monster whose types are being used to
        calculate it.
        opponent (Monster): The opponent whose types are being used to
        calculate it.

    Returns:
        float: The final multiplier that represents the effectiveness of
        the monster'stypes against the opponent's types.
    """
    multiplier = 1.0
    for _monster in monster_types:
        for _opponent in opponent_types:
            if _opponent and not (
                _monster.slug == "aether" or _opponent.slug == "aether"
            ):
                multiplier *= _monster.lookup_multiplier(_opponent.slug)
    return multiplier


def simple_damage_calculate(
    technique: Technique,
    user: Monster,
    target: Monster,
    additional_factors: Optional[dict[str, float]] = None,
) -> tuple[int, float]:
    """
    Calculates the damage of a technique based on stats and multiplier.

    Parameters:
        technique: The technique to calculate for.
        user: The user of the technique.
        target: The one the technique is being used on.
        additional_factors: A dictionary of additional factors to apply to
        the damage multiplier (default None)

    Returns:
        A tuple (damage, multiplier).
    """
    range_map = Loader.get_range_map("range_map.yaml")

    if technique.range not in range_map:
        logger.error(
            f"Unhandled damage category for technique '{technique.name}': {technique.range}"
        )
        return 0, 0.0

    range_map_entry = range_map[technique.range]

    user_strength: float = 0
    user_stat = range_map_entry.user_stat
    if user_stat.stat == "level":
        user_strength += (pre.COEFF_DAMAGE + user.level) * user_stat.weight
    else:
        user_strength += (
            getattr(user, user_stat.stat, 0)
            * (pre.COEFF_DAMAGE + user.level)
            * user_stat.weight
        )
    logger.debug(f"User strength: {user_strength}")

    target_resist: float = 0
    target_stat = range_map_entry.target_stat
    if target_stat.stat == "resist":
        target_resist += 1 * target_stat.weight
    else:
        target_resist += (
            getattr(target, target_stat.stat, 0) * target_stat.weight
        )
    logger.debug(f"Target resistance: {target_resist}")

    target_resist = max(1, target_resist)
    logger.debug(
        f"Target resistance (after preventing division by zero): {target_resist}"
    )

    mult = simple_damage_multiplier(
        (technique.types), (target.types), additional_factors
    )
    logger.debug(f"Damage multiplier: {mult}")

    move_strength = technique.power * mult
    logger.debug(f"Move strength: {move_strength}")

    damage = int(user_strength * move_strength / target_resist)
    logger.debug(f"Final damage: {damage}")
    return damage, mult


def weakest_link(modifiers: list[Modifier], monster: Monster) -> float:
    """
    Returns the smallest damage multiplier that applies to the given
    monster.

    This function iterates over the damage modifiers and checks if the
    monster's type matches any of the modifier's values. If a match is
    found, the function updates the multiplier to the smallest value
    found.

    Parameters:
        modifiers: A list of damage modifiers.
        monster: The monster to check.

    Returns:
        The smallest damage multiplier that applies to the monster.
    """
    multiplier: float = 1.0
    if modifiers:
        for modifier in modifiers:
            if modifier.attribute == "type":
                if any(t.name in modifier.values for t in monster.types):
                    multiplier = min(multiplier, modifier.multiplier)
            elif modifier.attribute == "tag":
                if any(t in modifier.values for t in monster.tags):
                    multiplier = min(multiplier, modifier.multiplier)
            else:
                raise ValueError(f"{modifier.attribute} isn't implemented.")
    return multiplier


def strongest_link(modifiers: list[Modifier], monster: Monster) -> float:
    """
    Returns the largest damage multiplier that applies to the given
    monster.

    This function iterates over the damage modifiers and checks if the
    monster's type matches any of the modifier's values. If a match is
    found, the function updates the multiplier to the largest value found.

    Parameters:
        modifiers: A list of damage modifiers.
        monster: The monster to check.

    Returns:
        The largest damage multiplier that applies to the monster.
    """
    multiplier: Optional[float] = None
    if modifiers:
        for modifier in modifiers:
            if modifier.attribute == "type":
                if any(t.name in modifier.values for t in monster.types):
                    multiplier = (
                        max(multiplier, modifier.multiplier)
                        if multiplier is not None
                        else modifier.multiplier
                    )
            elif modifier.attribute == "tag":
                if any(t in modifier.values for t in monster.tags):
                    multiplier = (
                        max(multiplier, modifier.multiplier)
                        if multiplier is not None
                        else modifier.multiplier
                    )
            else:
                raise ValueError(f"{modifier.attribute} isn't implemented.")
    return multiplier if multiplier is not None else 1.0


def cumulative_damage(modifiers: list[Modifier], monster: Monster) -> float:
    """
    Returns the cumulative product of all applicable damage multipliers for
    the given monster.

    This function iterates over the damage modifiers and checks if the monster's
    type matches any of the modifier's values. If a match is found, the function
    multiplies the current multiplier with the modifier's multiplier.

    Parameters:
        modifiers: A list of damage modifiers.
        monster: The monster to check.

    Returns:
        The cumulative product of all applicable damage multipliers.
    """
    multiplier: float = 1.0
    if modifiers:
        for modifier in modifiers:
            if modifier.attribute == "type":
                if any(t.name in modifier.values for t in monster.types):
                    multiplier *= modifier.multiplier
            elif modifier.attribute == "tag":
                if any(t in modifier.values for t in monster.tags):
                    multiplier *= modifier.multiplier
            else:
                raise ValueError(f"{modifier.attribute} isn't implemented.")
    return multiplier


def average_damage(modifiers: list[Modifier], monster: Monster) -> float:
    """
    Returns the average of all applicable damage multipliers for the given
    monster.

    This function iterates over the damage modifiers and checks if the monster's
    type matches any of the modifier's values. If a match is found, the function
    adds the modifier's multiplier to a list and calculates the average at the
    end.

    Parameters:
        modifiers: A list of damage modifiers.
        monster: The monster to check.

    Returns:
        The average of all applicable damage multipliers.
    """
    applicable_modifiers = []
    if modifiers:
        for modifier in modifiers:
            if modifier.attribute == "type":
                if any(t.name in modifier.values for t in monster.types):
                    applicable_modifiers.append(modifier.multiplier)
            elif modifier.attribute == "tag":
                if any(t in modifier.values for t in monster.tags):
                    applicable_modifiers.append(modifier.multiplier)
            else:
                raise ValueError(f"{modifier.attribute} isn't implemented.")

    if applicable_modifiers:
        return sum(applicable_modifiers) / len(applicable_modifiers)
    else:
        return 1.0


def first_applicable_damage(
    modifiers: list[Modifier], monster: Monster
) -> float:
    """
    Returns the first applicable damage multiplier for the given monster.

    This function iterates over the damage modifiers and checks if the monster's
    type matches any of the modifier's values. If a match is found, the function
    returns the modifier's multiplier immediately.

    Parameters:
        modifiers: A list of damage modifiers.
        monster: The monster to check.

    Returns:
        The first applicable damage multiplier.
    """
    if modifiers:
        for modifier in modifiers:
            if modifier.attribute == "type":
                if any(t.name in modifier.values for t in monster.types):
                    return modifier.multiplier
            elif modifier.attribute == "tag":
                if any(t in modifier.values for t in monster.tags):
                    return modifier.multiplier
            else:
                raise ValueError(f"{modifier.attribute} isn't implemented.")
    return 1.0


def simple_heal(
    technique: Technique,
    monster: Monster,
    additional_factors: Optional[dict[str, float]] = None,
) -> int:
    """
    Calculates the simple healing amount based on the technique's healing
    power and the monster's level.

    Parameters:
        technique: The technique being used.
        monster: The monster being healed.
        additional_factors: A dictionary of additional factors to apply to
        the healing amount (default None)

    Returns:
        int: The calculated healing amount.
    """
    base_heal = pre.COEFF_DAMAGE + monster.level * technique.healing_power
    if additional_factors:
        factor_multiplier = math.prod(additional_factors.values())
        base_heal = base_heal * factor_multiplier
    return int(base_heal)


def calculate_time_based_multiplier(
    hour: int,
    peak_hour: int,
    max_multiplier: float,
    start: int,
    end: int,
) -> float:
    """
    Calculate the multiplier based on the given hour and peak hour.

    Parameters:
        hour: The current hour.
        peak_hour: The peak hour.
        max_multiplier: The maximum power.
        start: The start hour of the period.
        end: The end hour of the period.

    Returns:
        float: The calculated multiplier.
    """
    if end < start:
        end += 24
    if hour < start:
        hour += 24
    if peak_hour < start:
        peak_hour += 24
    if (end or hour or peak_hour) > 47:
        return 0.0

    if start <= hour < end:
        distance_from_peak = abs(hour - peak_hour)
        if distance_from_peak > (end - start) / 2:
            distance_from_peak = (end - start) - distance_from_peak
        weighted_power = max_multiplier * (
            1 - (distance_from_peak / ((end - start) / 2)) ** 2
        )
        return max(weighted_power, 0.0)
    else:
        return 0.0


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


def update_stat(
    stat_name: str,
    stat_value: int,
    taste_warm: Optional[Taste],
    taste_cold: Optional[Taste],
) -> int:
    """
    It returns a bonus / malus of the stat based on additional parameters.
    """
    modified_stat = float(stat_value)

    if taste_cold:
        for modifier in taste_cold.modifiers:
            if stat_name in modifier.values:
                logger.debug(
                    f"Applying modifier: {modifier.multiplier} for {stat_name}"
                )
                modified_stat *= modifier.multiplier

    if taste_warm:
        for modifier in taste_warm.modifiers:
            if stat_name in modifier.values:
                logger.debug(
                    f"Applying modifier: {modifier.multiplier} for {stat_name}"
                )
                modified_stat *= modifier.multiplier

    return int(modified_stat)


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
    Calculates the shake_check value used to determine capture success.

    Parameters:
        target: The monster being captured.
        status_modifier: Modifier based on the monster's status condition.
        tuxeball_modifier: Modifier based on the type of capture device.

    Returns:
        The shake_check value.
    """
    config_capture = Loader.get_config_capture("config_capture.yaml")
    max_catch_rate = pre.CATCH_RATE_RANGE[1]
    shake_constant = config_capture.shake_constant
    shake_denominator = config_capture.shake_denominator
    shake_divisor = config_capture.shake_divisor
    hp_multiplier = config_capture.shake_hp_multiplier
    current_hp_multiplier = config_capture.shake_current_hp_multiplier
    hp_divisor = config_capture.shake_hp_divisor

    # Calculate catch_check using Generation III-IV formula
    # Reference: http://bulbapedia.bulbagarden.net/wiki/Catch_rate#Capture_method_.28Generation_VI.29
    # Approximate capture rate is catch_check / 255
    catch_check = (
        (hp_multiplier * target.hp - current_hp_multiplier * target.current_hp)
        * target.catch_rate
        * status_modifier
        * tuxeball_modifier
        / (hp_divisor * target.hp)
    )
    # Compute shake_check based on the catch_check value
    shake_check = shake_constant / (
        math.sqrt(math.sqrt(max_catch_rate / catch_check)) * shake_denominator
    )
    # Introduce random variability using catch_resistance
    # catch_resistance adjusts shake_check slightly for each capture attempt
    catch_resistance = random.uniform(
        target.lower_catch_resistance, target.upper_catch_resistance
    )
    shake_check *= catch_resistance

    # Debugging: Log detailed calculations for troubleshooting
    logger.debug("--- Debugging Capture Calculations ---")
    logger.debug(
        f"Capture formula: ({hp_multiplier} * target.hp - {current_hp_multiplier} * target.current_hp) * "
        f"target.catch_rate * status_modifier * tuxeball_modifier / ({hp_divisor} * target.hp)"
    )
    logger.debug(
        f"target.hp: {target.hp}, target.current_hp: {target.current_hp}, "
        f"target.catch_rate: {target.catch_rate}, status_modifier: {status_modifier}, "
        f"tuxeball_modifier: {tuxeball_modifier}"
    )
    logger.debug(f"Calculated catch_check: {catch_check}")
    logger.debug("--- Shake Check Calculation ---")
    logger.debug(
        f"shake_constant: {shake_constant}, shake_denominator: {shake_denominator}, "
        f"max_catch_rate: {max_catch_rate}"
    )
    logger.debug(
        f"Shake formula: {shake_constant}/(sqrt(sqrt(max_catch_rate/catch_check))"
        f"*{shake_denominator})"
    )
    logger.debug(f"Final shake_check value: {round(shake_check, 2)}")

    shake_chance = round((shake_constant - shake_check) / shake_constant, 2)
    logger.debug("--- Final Shake Statistics ---")
    logger.debug(
        f"shake_check: {round(shake_check)}, "
        f"Chance to break free per shake: {shake_chance}/{shake_divisor}"
    )
    return shake_check


def capture(shake_check: float) -> tuple[bool, int]:
    """
    Determines if the wild monster is successfully captured or escapes.

    Parameters:
        shake_check: The calculated value used in capture evaluation.

    Returns:
        (True) if the monster is captured.
        (False) if the monster escapes after a specific number of shakes.
    """
    config_capture = Loader.get_config_capture("config_capture.yaml")
    total_shakes = config_capture.total_shakes
    shake_divisor = config_capture.shake_divisor

    for i in range(0, total_shakes):
        random_num = random.randint(0, shake_divisor)
        logger.debug(f"shake check {i}: random number {random_num}")
        if random_num > int(shake_check):
            return (False, i + 1)
    return (True, total_shakes)


def relative_escape(user: Monster, target: Monster) -> bool:
    monster_strength = (target.melee + target.ranged + target.dodge) / 3
    level_advantage = user.level - target.level
    escape_chance = (
        0.2
        + (0.1 * level_advantage)
        - (0.05 * monster_strength / 10)
        + (0.05 * user.speed / 10)
    )
    escape_chance = max(0, min(escape_chance, 1))
    return random.random() <= escape_chance


def default_escape(user: Monster, target: Monster, attempts: int) -> bool:
    escape_chance = 0.4 + (0.15 * (attempts + user.level - target.level))
    return random.random() <= escape_chance


def attempt_escape(
    method: str, user: Monster, target: Monster, attempts: int
) -> bool:
    """
    Attempt to escape from a target monster.

    Parameters:
        method: The escape method to use.
        user: The monster attempting to escape.
        target: The monster from which the user is attempting to escape.
        attempts: The number of attempts the user has made to escape so far.

    Returns:
        True if the escape is successful, False otherwise.

    Raises:
        ValueError: If the specified method is not supported.
    """
    if method == "default":
        return default_escape(user, target, attempts)
    elif method == "relative":
        return relative_escape(user, target)
    elif method == "always":
        return True
    elif method == "never":
        return False
    else:
        raise ValueError(f"A formula for {method} doesn't exist.")


def speed_monster(monster: Monster, technique: Technique) -> int:
    """
    Calculate the speed modifier for the given monster / technique.
    """
    multiplier_speed = pre.MULTIPLIER_SPEED
    base_speed = float(monster.speed)
    base_speed_bonus = multiplier_speed if technique.is_fast else 1.0
    speed_modifier = base_speed * base_speed_bonus

    # Add a controlled random element
    speed_offset = pre.SPEED_OFFSET
    random_offset = random.uniform(-speed_offset, speed_offset)
    speed_modifier += random_offset

    # Ensure the speed modifier is not negative
    speed_modifier = max(speed_modifier, 1)
    # Use dodge as a tiebreaker
    speed_modifier += float(monster.dodge) * 0.01

    return int(speed_modifier)
