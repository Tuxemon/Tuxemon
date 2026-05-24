# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tuxemon.database.rules import (
    CaptureDeviceEffect,
    config_capdev,
    config_capture,
    config_combat,
    config_monster,
    range_map,
)
from tuxemon.platform.const.sizes import (
    COEFF_DAMAGE,
    COEFF_FEET,
    COEFF_MILES,
    COEFF_POUNDS,
)

if TYPE_CHECKING:
    from tuxemon.element import Element
    from tuxemon.entity.npc import NPC
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


def simple_damage_multiplier(
    attack_types: Sequence[Element],
    target_types: Sequence[Element],
    additional_factors: dict[str, float] | None = None,
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
    from tuxemon.element import ElementTypesHandler

    multiplier = ElementTypesHandler.calculate_affinity_score(
        attack_types, target_types
    )
    min_range, max_range = config_combat.multiplier_range
    multiplier = min(max_range, max(min_range, multiplier))

    if additional_factors:
        multiplier *= math.prod(additional_factors.values())

    return multiplier


def simple_damage_calculate(
    technique: Technique,
    user: Monster,
    target: Monster,
    additional_factors: dict[str, float] | None = None,
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

    if technique.range not in range_map:
        logger.error(
            f"Unhandled damage category for technique '{technique.name}': {technique.range}"
        )
        return 0, 0.0

    range_map_entry = range_map[technique.range]

    user_combat_stats = user.get_combat_stats()
    target_combat_stats = target.get_combat_stats()

    logger.debug(
        f"--- Damage calculation: {user.name} uses {technique.name} on {target.name} ---"
    )

    user_strength: float = 0
    user_stat = range_map_entry.user_stat
    if user_stat.stat == "level":
        raw_user_stat = user.level
        user_strength += (COEFF_DAMAGE + user.level) * user_stat.weight
    else:
        raw_user_stat = getattr(user_combat_stats, user_stat.stat, 0)
        user_strength += (
            raw_user_stat * (COEFF_DAMAGE + user.level) * user_stat.weight
        )
    logger.debug(
        f"  User: {user.name} Lv{user.level} | {user_stat.stat}={raw_user_stat} "
        f"| user_strength = ({COEFF_DAMAGE}+{user.level}) * {raw_user_stat} * {user_stat.weight} = {user_strength}"
    )

    target_resist: float = 0
    target_stat = range_map_entry.target_stat
    if target_stat.stat == "resist":
        raw_target_stat = 1
        target_resist += 1 * target_stat.weight
    else:
        raw_target_stat = getattr(target_combat_stats, target_stat.stat, 0)
        target_resist += raw_target_stat * target_stat.weight
    logger.debug(
        f"  Target: {target.name} | {target_stat.stat}={raw_target_stat} "
        f"| target_resist = {raw_target_stat} * {target_stat.weight} = {target_resist}"
    )

    target_resist = max(1, target_resist)
    logger.debug(f"  target_resist (floor 1): {target_resist}")

    mult = simple_damage_multiplier(
        (technique.types.current), (target.types.current), additional_factors
    )
    logger.debug(
        f"  Types: {[t.slug for t in technique.types.current]} vs "
        f"{[t.slug for t in target.types.current]} | multiplier={mult}"
    )

    move_strength = technique.power * mult
    logger.debug(
        f"  move_strength = power({technique.power}) * mult({mult}) = {move_strength}"
    )

    damage = int(user_strength * move_strength / target_resist)
    logger.debug(
        f"  damage = int({user_strength} * {move_strength} / {target_resist}) = {damage}"
    )

    user_statuses = [s.slug for s in user.status.get_statuses()]
    target_statuses = [s.slug for s in target.status.get_statuses()]

    status_part = ""
    if user_statuses:
        status_part += f" user_status={user_statuses}"
    if target_statuses:
        status_part += f" target_status={target_statuses}"

    logger.info(
        f"[COMBAT] {user.name} Lv{user.level} -[{technique.name}]-> {target.name} | "
        f"range={technique.range} power={technique.power} mult={mult:.2f} "
        f"user_str={user_strength:.1f} target_res={target_resist:.1f}"
        f"{status_part} => {damage} dmg"
    )
    return damage, mult



def simple_heal(
    technique: Technique,
    monster: Monster,
    additional_factors: dict[str, float] | None = None,
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
    base_heal = COEFF_DAMAGE + monster.level * technique.healing_power
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
    heal = min(target.hp // divisor, target.missing_hp)
    return heal


def calculate_hp_transfer(user: Monster, target: Monster, divisor: int) -> int:
    """
    Calculates the amount of HP transferred from one monster to another.

    Parameters:
        user: The monster receiving HP.
        target: The monster donating HP.
        divisor: Scaling factor based on target's max HP.

    Returns:
        The amount of HP to be transferred, capped by target's current HP
        and user's missing HP.
    """
    heal = min(target.hp // divisor, target.current_hp, user.missing_hp)
    return heal


def set_health(
    monster: Monster, value: float | int, adjust: bool = False
) -> None:
    """Sets or adjusts monster's health, ensuring valid limits."""
    if adjust:
        monster.current_hp += (
            int(monster.hp * value) if isinstance(value, float) else int(value)
        )
    else:
        monster.current_hp = (
            int(monster.hp * value) if isinstance(value, float) else int(value)
        )

    monster.current_hp = max(0, min(monster.current_hp, monster.hp))

    if monster.is_fainted:
        monster.current_hp = 0


def set_weight(monster: Monster, value: float) -> float:
    """
    Sets a personalized weight for each monster.
    If the current weight already matches the provided value, it remains unchanged.
    Otherwise, it calculates a random weight within the allowed range.
    """
    if monster.weight == value:
        return value
    _minor, _major = config_monster.weight_range
    min_weight = value * (1 + _minor)
    max_weight = value * (1 + _major)
    return round(random.uniform(min_weight, max_weight), 2)


def set_height(monster: Monster, value: float) -> float:
    """
    Sets a personalized height for each monster.
    If the current height already matches the provided value, it remains unchanged.
    Otherwise, it calculates a random height within the allowed range.
    """
    if monster.height == value:
        return value
    _minor, _major = config_monster.height_range
    min_height = value * (1 + _minor)
    max_height = value * (1 + _major)
    return round(random.uniform(min_height, max_height), 2)


def convert_lbs(kg: float) -> int:
    """It converts kilograms into pounds."""
    return round(kg * COEFF_POUNDS)


def convert_ft(cm: float) -> int:
    """It converts centimeters into feet."""
    return round(cm * COEFF_FEET)


def convert_km(steps: float) -> float:
    """It converts steps into kilometers."""
    return round(steps / 1000, 2)


def convert_mi(steps: float) -> float:
    """It converts steps into miles."""
    km = convert_km(steps)
    return round(km * COEFF_MILES, 2)


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
    max_catch_rate = config_monster.catch_rate_range[1]
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
    total_shakes = config_capture.total_shakes
    shake_divisor = config_capture.shake_divisor

    for i in range(0, total_shakes):
        random_num = random.randint(0, shake_divisor)
        logger.debug(f"shake check {i}: random number {random_num}")
        if random_num > int(shake_check):
            return (False, i + 1)
    return (True, total_shakes)


def calculate_status_modifier(item: Item, target: Monster) -> float:
    config = config_capdev.items.get(item.slug)
    status_modifier = config_capdev.status_modifier

    status = target.status.current_status
    if config is None or status is None:
        return status_modifier

    logger.debug(f"Base status_modifier: {status_modifier}")
    logger.debug(f"Negative modifier: {config.negative_modifier}")
    logger.debug(f"Positive modifier: {config.positive_modifier}")
    logger.debug(f"Specific modifiers: {config.specific_status_modifiers}")

    negative_modifier = config.negative_modifier
    positive_modifier = config.positive_modifier
    specific_status = config.specific_status_modifiers

    for status in target.status.get_statuses():
        if specific_status and status.slug in specific_status:
            specific_modifier = specific_status[status.slug]
            logger.debug(
                f"Specific modifier found for status '{status.slug}': {specific_modifier}"
            )
            status_modifier *= specific_modifier

        if status.category:
            category_modifier = (
                negative_modifier
                if status.category == "negative"
                else positive_modifier
            )
            logger.debug(
                f"Applying category modifier for '{status.category}': {category_modifier}"
            )
            status_modifier *= category_modifier

    logger.debug(
        f"Final status_modifier for item '{item.slug}' and target '{target.slug}': {status_modifier}"
    )
    return status_modifier


def calculate_capdev_modifier(
    item: Item, target: Monster, character: NPC
) -> float:
    config = config_capdev.items.get(item.slug)
    capdev_modifier = config_capdev.capdev_modifier

    if config is None:
        return capdev_modifier

    specific_capdev_modifier = config.specific_capdev_modifier

    if specific_capdev_modifier:
        logger.debug(
            f"Specific capdev_modifier found for item '{item.slug}': {specific_capdev_modifier}"
        )
        capdev_modifier *= specific_capdev_modifier

    if item.slug == "tuxeball_crusher":
        crusher = ((target.armour / 5) * 0.01) + 1
        if crusher >= 1.4:
            crusher = 1.4
        if calculate_status_modifier(item, target) == config.positive_modifier:
            crusher = 0.01
        capdev_modifier *= crusher

    specific_element_modifiers = config.specific_element_modifiers

    if specific_element_modifiers:
        logger.debug(
            f"Checking specific element modifiers for item '{item.slug}' and target types"
        )
        for slug, modifier in specific_element_modifiers.items():
            if target.has_type(slug):
                logger.debug(
                    f"Target matches element '{slug}'. Applying modifier: {modifier}"
                )
                capdev_modifier *= modifier
        logger.debug(
            "No matching element found. Applying fallback_element_malus"
        )
        capdev_modifier *= config.fallback_element_malus

    specific_gender_modifiers = config.specific_gender_modifiers

    if specific_gender_modifiers:
        logger.debug(
            f"Checking specific gender modifiers for item '{item.slug}' and target gender '{target.gender}'"
        )
        for slug, modifier in specific_gender_modifiers.items():
            if target.gender == slug:
                logger.debug(
                    f"Target matches gender '{slug}'. Applying modifier: {modifier}"
                )
                capdev_modifier *= modifier
        logger.debug(
            "No matching gender found. Applying fallback_gender_malus"
        )
        capdev_modifier *= config.fallback_gender_malus

    specific_variables_modifiers = config.specific_variables_modifiers

    if specific_variables_modifiers:
        logger.debug(
            f"Checking specific variable modifiers for item '{item.slug}' and target game variables"
        )
        for variables in specific_variables_modifiers:
            if (
                not isinstance(variables, dict)
                or "key" not in variables
                or "value" not in variables
            ):
                logger.warning(f"Invalid variables structure: {variables}")
                continue

            if character.variable_manager.check_logic(
                [{variables["key"]: variables["value"]}]
            ):
                logger.debug(
                    f"Variable match for key '{variables['key']}' == {variables['value']}. "
                    f"Applying fallback_variables_bonus"
                )
                capdev_modifier *= config.fallback_variables_bonus

        logger.debug(
            "No matching variable found. Applying fallback_variables_malus"
        )
        capdev_modifier *= config.fallback_variables_malus

    random_bounds = config.random_bounds

    if random_bounds:
        random_value = random.uniform(random_bounds[0], random_bounds[1])
        logger.debug(
            f"Using random bounds {random_bounds}. Generated random value: {random_value}"
        )
        capdev_modifier *= random_value

    logger.debug(
        f"Returning final capdev_modifier for item '{item.slug}': {capdev_modifier}"
    )
    return capdev_modifier


def on_capture_fail(item: Item, target: Monster, character: NPC) -> None:
    config = config_capdev.items.get(item.slug)
    if config is None:
        return

    if config.capdev_persistent_on_failure:
        tuxeball = character.bag.find_item(item.slug)
        if tuxeball:
            tuxeball.increase_quantity()


def on_capture_success(item: Item, target: Monster, character: NPC) -> None:
    config = config_capdev.items.get(item.slug)
    if config is None:
        return

    if config.capdev_persistent_on_success:
        tuxeball = character.bag.find_item(item.slug)
        if tuxeball:
            tuxeball.increase_quantity()

    if config.capdev_effects:
        apply_effects(config.capdev_effects, target)


def apply_effects(config: list[CaptureDeviceEffect], target: Monster) -> None:
    for effect in config:
        target_attr = effect.target_attribute
        operation = effect.operation
        value = effect.value

        if operation == "increment" and isinstance(value, int):
            setattr(target, target_attr, getattr(target, target_attr) + value)
        elif operation == "decrement" and isinstance(value, int):
            setattr(target, target_attr, getattr(target, target_attr) - value)
        elif operation == "multiply" and isinstance(value, int):
            setattr(target, target_attr, getattr(target, target_attr) * value)
        elif operation == "divide" and isinstance(value, int):
            setattr(target, target_attr, getattr(target, target_attr) / value)
        elif operation == "set" and isinstance(value, str):
            setattr(target, target_attr, value)
        else:
            raise ValueError(f"Unsupported operation: {operation}")


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
    min_mod = max(config_combat.min_speed_modifier, 1)
    combat_stats = monster.get_combat_stats()
    base_speed = float(max(combat_stats.speed, 0))

    # Calculate modifier based on technique speed
    speed_adjustment = technique.speed * config_combat.speed_factor
    speed_bonus = config_combat.base_speed_bonus + speed_adjustment

    # Base calculation
    speed_modifier = base_speed * speed_bonus

    # Ensure minimum bound
    speed_modifier = max(speed_modifier, min_mod)

    # Use dodge as a strategic tiebreaker
    speed_modifier += (
        max(float(combat_stats.dodge), 0) * config_combat.dodge_modifier
    )

    return int(speed_modifier)


def modify_monster_custom_stat(
    monster: Monster, stat: str, value: float, operation: str
) -> None:
    """
    Helper method to modify a monster's stat based on the specified operation.

    Parameters:
        monster: The monster instance.
        stat: The stat to modify.
        value: The value to apply.
        operation: "add" for integer addition, "multiply" for float scaling.
    """
    logger.debug(f"{value} {operation} operation on {stat}")

    if not hasattr(monster.custom_stats, stat):
        raise AttributeError(f"Unknown stat '{stat}'")

    current_value = getattr(monster.custom_stats, stat)

    if operation == "add":
        new_value = current_value + int(value)
    elif operation == "multiply":
        base_value = getattr(monster, stat) * value
        new_value = current_value + int(base_value)
    else:
        raise ValueError(f"Invalid operation: {operation}")

    setattr(monster.custom_stats, stat, new_value)
    monster.set_stats()


def modify_technique_custom_stat(
    tech: Technique, stat: str, value: float, operation: str
) -> None:
    """
    Permanently modify a technique's custom boosts.

    Parameters:
        tech: The Technique instance.
        stat: One of: "power", "potency", "accuracy", "healing_power".
        value: The value to apply.
        operation: "add" or "multiply".
    """
    logger.debug(
        f"{value} {operation} operation on technique custom stat '{stat}'"
    )

    if not hasattr(tech.custom_boosts, stat):
        raise AttributeError(f"Unknown stat '{stat}'")

    current_value = getattr(tech.custom_boosts, stat)

    if operation == "add":
        new_value = current_value + value
    elif operation == "multiply":
        base_value = getattr(tech.base_stats, stat)
        new_value = current_value + (base_value * value)
    else:
        raise ValueError(f"Invalid operation: {operation}")

    setattr(tech.custom_boosts, stat, new_value)
    tech.reset_current_stats()