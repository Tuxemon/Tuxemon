# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
from unittest.mock import MagicMock

import pytest

from tuxemon.database.rules import config_combat, config_monster
from tuxemon.element import Element, ElementTypesHandler
from tuxemon.formula import (
    calculate_time_based_multiplier,
    modify_monster_custom_stat,
    modify_technique_custom_stat,
    set_health,
    set_height,
    set_weight,
    simple_damage_calculate,
    simple_damage_multiplier,
    simple_heal,
)
from tuxemon.monster.monster import Monster
from tuxemon.monster.stats import BasicStats, CustomStatBoosts
from tuxemon.platform.const.sizes import COEFF_DAMAGE
from tuxemon.technique.stats import (
    TechniqueBaseStats,
    TechniqueCustomBoosts,
)
from tuxemon.technique.technique import Technique


# TestSimpleHeal
@pytest.fixture
def heal_env():
    monster = MagicMock(spec=Monster)
    technique = MagicMock(spec=Technique)
    monster.level = 0.0
    technique.healing_power = 0.0
    return technique, monster


def test_simple_heal_no_factors(heal_env):
    tech, mon = heal_env
    tech.healing_power = 5
    mon.level = 10
    expected = COEFF_DAMAGE + mon.level * tech.healing_power
    assert simple_heal(tech, mon) == int(expected)


def test_simple_heal_with_factors(heal_env):
    tech, mon = heal_env
    tech.healing_power = 3
    mon.level = 15
    factors = {"boost": 1.2, "penalty": 0.8}
    expected = (COEFF_DAMAGE + mon.level * tech.healing_power) * math.prod(
        factors.values()
    )
    assert simple_heal(tech, mon, factors) == int(expected)


def test_simple_heal_empty_factors(heal_env):
    tech, mon = heal_env
    tech.healing_power = 2
    mon.level = 20
    expected = COEFF_DAMAGE + mon.level * tech.healing_power
    assert simple_heal(tech, mon, {}) == int(expected)


# TestCalculateTimeBasedMultiplier
@pytest.mark.parametrize(
    "args,expected",
    [
        pytest.param((12, 12, 1.5, 8, 20), 1.5, id="base"),
        pytest.param((2, 12, 1.5, 8, 20), 0.0, id="low_start"),
        pytest.param((-5, -10, 1.5, -8, -2), 0.0, id="negative_values"),
        pytest.param((12, 12, 0, 8, 20), 0.0, id="zero_multiplier"),
    ],
)
def test_time_based_multiplier(args, expected):
    assert calculate_time_based_multiplier(*args) == expected


# TestSetWeight
@pytest.fixture
def weight_env():
    monster = MagicMock(spec=Monster, weight=0)
    minor, major = config_monster.weight_range
    return monster, minor, major


def test_set_weight_zero(weight_env):
    mon, minor, major = weight_env
    assert set_weight(mon, 0) == 0


def test_set_weight_positive(weight_env):
    mon, minor, major = weight_env
    w = set_weight(mon, 100)
    assert w >= 100 * (1 + minor)
    assert w <= 100 * (1 + major)


def test_set_weight_negative(weight_env):
    mon, minor, major = weight_env
    w = set_weight(mon, -50)
    assert w >= -50 * (1 + major)
    assert w <= -50 * (1 + minor)


def test_set_weight_randomness(weight_env):
    mon, minor, major = weight_env
    weights = [set_weight(mon, 75) for _ in range(100)]
    assert len(set(weights)) >= 1


# TestSetHeight
@pytest.fixture
def height_env():
    monster = MagicMock(spec=Monster, height=0)
    minor, major = config_monster.height_range
    return monster, minor, major


def test_set_height_zero(height_env):
    mon, minor, major = height_env
    assert set_height(mon, 0) == 0


def test_set_height_positive(height_env):
    mon, minor, major = height_env
    h = set_height(mon, 100)
    assert h >= 100 * (1 + minor)
    assert h <= 100 * (1 + major)


def test_set_height_negative(height_env):
    mon, minor, major = height_env
    h = set_height(mon, -50)
    assert h >= -50 * (1 + major)
    assert h <= -50 * (1 + minor)


def test_set_height_randomness(height_env):
    mon, minor, major = height_env
    heights = [set_height(mon, 75) for _ in range(100)]
    assert len(set(heights)) >= 1


# TestSimpleDamageMultiplier
@pytest.fixture
def elements():
    ElementTypesHandler.clear_cache()
    fire = MagicMock(spec=Element)
    fire.slug = "fire"
    water = MagicMock(spec=Element)
    water.slug = "water"
    grass = MagicMock(spec=Element)
    grass.slug = "grass"
    normal = MagicMock(spec=Element)
    normal.slug = "normal"
    return fire, water, grass, normal


def test_basic_multiplier(elements):
    fire, water, *_ = elements
    fire.lookup_multiplier = MagicMock(return_value=2.0)
    assert simple_damage_multiplier([fire], [water]) == 2.0


@pytest.mark.parametrize(
    "vals,expected",
    [
        pytest.param((2.0, 0.5), 1.0, id="pair"),
    ],
)
def test_multiple_attack_types(elements, vals, expected):
    fire, water, grass, _ = elements
    fire.lookup_multiplier = MagicMock(return_value=vals[0])
    grass.lookup_multiplier = MagicMock(return_value=vals[1])
    assert simple_damage_multiplier([fire, grass], [water]) == expected


def test_multiple_target_types(elements):
    fire, water, grass, _ = elements
    fire.lookup_multiplier = MagicMock(side_effect=[2.0, 0.5])
    assert simple_damage_multiplier([fire], [water, grass]) == 1.0


def test_additional_factors(elements):
    fire, water, *_ = elements
    fire.lookup_multiplier = MagicMock(return_value=2.0)
    factors = {"boost": 1.5, "nerf": 0.8}
    assert round(simple_damage_multiplier([fire], [water], factors), 1) == 2.4


@pytest.mark.parametrize(
    "atk,tgt",
    [
        pytest.param([], ["water"], id="empty_atk"),
        pytest.param(["fire"], [], id="empty_tgt"),
    ],
)
def test_empty_attack_or_target(elements, atk, tgt):
    fire, water, *_ = elements
    atk = [fire] if atk else []
    tgt = [water] if tgt else []
    assert simple_damage_multiplier(atk, tgt) == 1.0


def test_clamping(elements):
    fire, water, *_ = elements
    fire.lookup_multiplier = MagicMock(return_value=10.0)
    mult = simple_damage_multiplier([fire], [water])
    _, max_range = config_combat.multiplier_range
    assert mult <= max_range


def test_cache_reuse(elements):
    fire, water, *_ = elements
    fire.lookup_multiplier = MagicMock(return_value=2.0)
    simple_damage_multiplier([fire], [water])
    mult = simple_damage_multiplier([fire], [water])
    fire.lookup_multiplier.assert_called_once()
    assert mult == 2.0


# TestSimpleDamageCalculate
@pytest.fixture
def dmg_env():
    tech = MagicMock()
    user = MagicMock()
    target = MagicMock()

    fire = MagicMock(spec=Element)
    fire.slug = "fire"
    water = MagicMock(spec=Element)
    water.slug = "water"

    user.level = 10
    tech.power = 50

    tech.types.current = [fire]
    fire.lookup_multiplier = MagicMock(return_value=2.0)

    target.types.current = [water]
    fire.lookup_multiplier = MagicMock(return_value=2.0)

    return tech, user, target


def test_valid_melee_damage(dmg_env):
    tech, user, target = dmg_env
    tech.range = "melee"
    user.get_combat_stats.return_value = BasicStats(melee=30)
    target.get_combat_stats.return_value = BasicStats(armour=20)
    dmg, mult = simple_damage_calculate(tech, user, target)
    assert isinstance(dmg, int)
    assert dmg > 0
    assert mult > 0.0


def test_valid_touch_damage(dmg_env):
    tech, user, target = dmg_env
    tech.range = "touch"
    user.get_combat_stats.return_value = BasicStats(melee=25)
    target.get_combat_stats.return_value = BasicStats(dodge=10)
    dmg, mult = simple_damage_calculate(tech, user, target)
    assert dmg > 0
    assert mult > 0.0


def test_additional_factors_applied(dmg_env):
    tech, user, target = dmg_env
    tech.range = "ranged"
    user.get_combat_stats.return_value = BasicStats(ranged=40)
    target.get_combat_stats.return_value = BasicStats(dodge=15)
    factors = {"weather_bonus": 0.2}
    dmg, mult = simple_damage_calculate(
        tech, user, target, additional_factors=factors
    )
    assert dmg > 0
    assert pytest.approx(mult, abs=0.2) == 0.2


def test_level_based_damage(dmg_env):
    tech, user, target = dmg_env
    tech.range = "reliable"
    user.level = 15
    target.resist = 3
    dmg, mult = simple_damage_calculate(tech, user, target)
    assert dmg > 0
    assert mult > 0.0


# TestModifyMonsterCustomStat
@pytest.fixture
def monster():
    m = MagicMock(spec=Monster)
    m.custom_stats = CustomStatBoosts()
    m.set_stats = MagicMock()
    return m


@pytest.mark.parametrize(
    "initial,amount,op,expected",
    [
        pytest.param(10, 5.0, "add", 15, id="add"),
    ],
)
def test_add_operation(monster, initial, amount, op, expected):
    monster.custom_stats.armour = initial
    modify_monster_custom_stat(monster, "armour", amount, op)
    assert monster.custom_stats.armour == expected
    monster.set_stats.assert_called_once()


@pytest.mark.parametrize(
    "base,initial,amount,op,expected",
    [
        pytest.param(10, 0, 1.5, "multiply", 15, id="multiply"),
    ],
)
def test_multiply_operation(monster, base, initial, amount, op, expected):
    monster.armour = base
    monster.custom_stats.armour = initial
    modify_monster_custom_stat(monster, "armour", amount, op)
    assert monster.custom_stats.armour == expected
    monster.set_stats.assert_called_once()


def test_invalid_operation(monster):
    with pytest.raises(ValueError):
        modify_monster_custom_stat(monster, "armour", 5.0, "invalid")


def test_unrecognized_stat(monster):
    with pytest.raises(AttributeError):
        modify_monster_custom_stat(monster, "unknown", 5.0, "add")


def test_modify_monster_custom_stat_calls_set_stats(monster):
    monster.custom_stats.armour = 10
    modify_monster_custom_stat(monster, "armour", 5.0, "add")
    monster.set_stats.assert_called_once()


# TestModifyTechniqueCustomStat
@pytest.fixture
def tech():
    t = MagicMock(spec=Technique)
    t.custom_boosts = TechniqueCustomBoosts()
    t.base_stats = TechniqueBaseStats(
        power=10.0,
        potency=5.0,
        accuracy=0.8,
        healing_power=3.0,
    )
    t.reset_current_stats = MagicMock()
    return t


@pytest.mark.parametrize(
    "initial,amount,op,expected",
    [
        pytest.param(10.0, 5.0, "add", 15.0, id="add"),
    ],
)
def test_add_operation_tech(tech, initial, amount, op, expected):
    tech.custom_boosts.power = initial
    modify_technique_custom_stat(tech, "power", amount, op)
    assert tech.custom_boosts.power == expected
    tech.reset_current_stats.assert_called_once()


@pytest.mark.parametrize(
    "initial,amount,op,expected",
    [
        pytest.param(0.0, 1.5, "multiply", 15.0, id="multiply"),
    ],
)
def test_multiply_operation_tech(tech, initial, amount, op, expected):
    tech.custom_boosts.power = initial
    modify_technique_custom_stat(tech, "power", amount, op)
    assert tech.custom_boosts.power == expected
    tech.reset_current_stats.assert_called_once()


def test_invalid_operation_tech(tech):
    with pytest.raises(ValueError):
        modify_technique_custom_stat(tech, "power", 5.0, "invalid")


def test_unrecognized_stat_tech(tech):
    with pytest.raises(AttributeError):
        modify_technique_custom_stat(tech, "unknown", 5.0, "add")


def test_modify_technique_custom_stat_calls_reset(tech):
    tech.custom_boosts.power = 10.0
    modify_technique_custom_stat(tech, "power", 5.0, "add")
    tech.reset_current_stats.assert_called_once()


# TestSetHealth
@pytest.fixture
def monster_hp():
    return MagicMock(spec=Monster, hp=100, current_hp=100, is_fainted=False)


def test_set_health_direct(monster_hp):
    set_health(monster_hp, 50)
    assert monster_hp.current_hp == 50


def test_set_health_percentage(monster_hp):
    set_health(monster_hp, 0.5)
    assert monster_hp.current_hp == 50


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(10, 100, id="add_10"),
    ],
)
def test_adjust_health_add(monster_hp, value, expected):
    set_health(monster_hp, value, adjust=True)
    assert monster_hp.current_hp == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(-30, 70, id="subtract_30"),
    ],
)
def test_adjust_health_subtract(monster_hp, value, expected):
    set_health(monster_hp, value, adjust=True)
    assert monster_hp.current_hp == expected


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(1.5, id="value_1_5"),
        pytest.param(9999, id="value_9999"),
    ],
)
def test_hp_max_limit(monster_hp, value):
    set_health(monster_hp, value)
    assert monster_hp.current_hp == monster_hp.hp


def test_faint_triggered_on_zero_hp(monster_hp):
    set_health(monster_hp, -200, adjust=True)
    assert monster_hp.current_hp == 0


def test_set_health_to_zero(monster_hp):
    monster_hp.is_fainted = True
    set_health(monster_hp, 0)
    assert monster_hp.current_hp == 0


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(-100, id="value_minus_100"),
        pytest.param(-200, id="value_minus_200"),
    ],
)
def test_hp_min_limit(monster_hp, value):
    monster_hp.is_fainted = True
    set_health(monster_hp, value, adjust=True)
    assert monster_hp.current_hp == 0


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0.5, id="percentage_50"),
        pytest.param(0.25, id="percentage_25"),
    ],
)
def test_set_health_percentage_param(monster_hp, value):
    set_health(monster_hp, value)
    assert monster_hp.current_hp == int(monster_hp.hp * value)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(50, id="cap_50"),
        pytest.param(200, id="cap_200"),
    ],
)
def test_adjust_health_cap(monster_hp, value):
    set_health(monster_hp, value, adjust=True)
    assert monster_hp.current_hp == monster_hp.hp
