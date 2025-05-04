# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import unittest
from unittest.mock import MagicMock

from tuxemon import prepare
from tuxemon.db import Modifier
from tuxemon.element import Element
from tuxemon.formula import (
    average_damage,
    calculate_time_based_multiplier,
    change_bond,
    config_monster,
    cumulative_damage,
    first_applicable_damage,
    modify_stat,
    set_health,
    set_height,
    set_weight,
    simple_damage_calculate,
    simple_damage_multiplier,
    simple_heal,
    strongest_link,
    update_stat,
    weakest_link,
)
from tuxemon.monster import Monster
from tuxemon.taste import Taste
from tuxemon.technique.technique import Technique


class TestUpdateStat(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster)
        self.monster.melee = 10.0
        self.monster.ranged = 10.0
        self.monster.dodge = 10.0

        self.salty_modifier = MagicMock(spec=Modifier)
        self.salty_modifier.attribute = "stat"
        self.salty_modifier.values = ["melee"]
        self.salty_modifier.multiplier = 1.1

        self.flakey_modifier = MagicMock(spec=Modifier)
        self.flakey_modifier.attribute = "stat"
        self.flakey_modifier.values = ["ranged"]
        self.flakey_modifier.multiplier = 0.9

        self.salty = MagicMock(spec=Taste)
        self.salty.slug = "salty"
        self.salty.modifiers = [self.salty_modifier]

        self.flakey = MagicMock(spec=Taste)
        self.flakey.slug = "flakey"
        self.flakey.modifiers = [self.flakey_modifier]

        self.monster.taste_warm = self.salty
        self.monster.taste_cold = self.flakey

    def test_update_stat_matching_taste_bonus(self):
        expected_bonus = int(
            self.monster.melee * self.salty_modifier.multiplier
        )
        bonus = update_stat("melee", self.monster.melee, self.salty, None)
        self.assertEqual(bonus, expected_bonus)

    def test_update_stat_matching_taste_malus(self):
        expected_malus = int(
            self.monster.ranged * self.flakey_modifier.multiplier
        )
        malus = update_stat("ranged", self.monster.ranged, None, self.flakey)
        self.assertEqual(malus, expected_malus)

    def test_update_stat_matching_taste_neuter(self):
        neuter = update_stat("dodge", self.monster.dodge, None, None)
        self.assertEqual(neuter, self.monster.dodge)


class TestSimpleHeal(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster)
        self.monster.level = 0.0
        self.technique = MagicMock(spec=Technique)
        self.technique.healing_power = 0.0

    def test_simple_heal_no_factors(self):
        self.technique.healing_power = 5
        self.monster.level = 10
        expected_heal = (
            prepare.COEFF_DAMAGE
            + self.monster.level * self.technique.healing_power
        )
        actual_heal = simple_heal(self.technique, self.monster)
        self.assertEqual(int(expected_heal), actual_heal)

    def test_simple_heal_with_factors(self):
        self.technique.healing_power = 3
        self.monster.level = 15
        factors = {"boost": 1.2, "penalty": 0.8}
        expected_multiplier = math.prod(factors.values())
        expected_heal = (
            prepare.COEFF_DAMAGE
            + self.monster.level * self.technique.healing_power
        ) * expected_multiplier
        actual_heal = simple_heal(self.technique, self.monster, factors)
        self.assertEqual(int(expected_heal), actual_heal)

    def test_simple_heal_empty_factors(self):
        self.technique.healing_power = 2
        self.monster.level = 20
        factors = {}
        expected_heal = (
            prepare.COEFF_DAMAGE
            + self.monster.level * self.technique.healing_power
        )
        actual_heal = simple_heal(self.technique, self.monster, factors)
        self.assertEqual(int(expected_heal), actual_heal)


class TestCalculateTimeBasedMultiplier(unittest.TestCase):
    def test_mid_peak(self):
        result = calculate_time_based_multiplier(12, 12, 1.5, 8, 20)
        self.assertEqual(result, 1.5)

    def test_peak_off(self):
        result = calculate_time_based_multiplier(2, 12, 1.5, 8, 20)
        self.assertEqual(result, 0.0)

    def test_negative_hours(self):
        result = calculate_time_based_multiplier(-5, -10, 1.5, -8, -2)
        self.assertEqual(result, 0.0)

    def test_zero_max_multiplier(self):
        result = calculate_time_based_multiplier(12, 12, 0, 8, 20)
        self.assertEqual(result, 0.0)


class TestSetWeight(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster, weight=0)
        self.minor, self.major = config_monster.weight_range

    def test_set_weight_zero(self):
        weight = set_weight(self.monster, 0)
        self.assertEqual(weight, 0)

    def test_set_weight_positive(self):
        weight = set_weight(self.monster, 100)
        self.assertGreaterEqual(weight, 100 * (1 + self.minor))
        self.assertLessEqual(weight, 100 * (1 + self.major))

    def test_set_weight_negative(self):
        weight = set_weight(self.monster, -50)
        self.assertGreaterEqual(weight, -50 * (1 + self.major))
        self.assertLessEqual(weight, -50 * (1 + self.minor))

    def test_set_weight_randomness(self):
        weights = [set_weight(self.monster, 75) for _ in range(100)]
        self.assertGreaterEqual(len(set(weights)), 1)


class TestSetHeight(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster, height=0)
        self.minor, self.major = config_monster.height_range

    def test_set_height_zero(self):
        height = set_height(self.monster, 0)
        self.assertEqual(height, 0)

    def test_set_height_positive(self):
        height = set_height(self.monster, 100)
        self.assertGreaterEqual(height, 100 * (1 + self.minor))
        self.assertLessEqual(height, 100 * (1 + self.major))

    def test_set_height_negative(self):
        height = set_height(self.monster, -50)
        self.assertGreaterEqual(height, -50 * (1 + self.major))
        self.assertLessEqual(height, -50 * (1 + self.minor))

    def test_set_height_randomness(self):
        heights = [set_height(self.monster, 75) for _ in range(100)]
        self.assertGreaterEqual(len(set(heights)), 1)


class TestSimpleDamageMultiplier(unittest.TestCase):
    def setUp(self):
        self.fire = MagicMock(spec=Element)
        self.fire.slug = "fire"
        self.water = MagicMock(spec=Element)
        self.water.slug = "water"
        self.grass = MagicMock(spec=Element)
        self.grass.slug = "grass"
        self.aether = MagicMock(spec=Element)
        self.aether.slug = "aether"

    def test_basic_multiplier(self):
        attack_type = self.fire
        target_type = self.water
        attack_type.lookup_multiplier = MagicMock(return_value=2.0)
        multiplier = simple_damage_multiplier([attack_type], [target_type])
        self.assertEqual(multiplier, 2.0)

    def test_multiple_attack_types(self):
        attack_types = [self.fire, self.grass]
        target_type = self.water
        attack_types[0].lookup_multiplier = MagicMock(return_value=2.0)
        attack_types[1].lookup_multiplier = MagicMock(return_value=0.5)
        multiplier = simple_damage_multiplier(attack_types, [target_type])
        self.assertEqual(multiplier, 0.5)

    def test_multiple_target_types(self):
        attack_type = self.fire
        target_types = [self.water, self.grass]
        attack_type.lookup_multiplier = MagicMock(side_effect=[2.0, 0.5])
        multiplier = simple_damage_multiplier([attack_type], target_types)
        self.assertEqual(multiplier, 2.0)

    def test_aether_type(self):
        attack_type = self.aether
        target_type = self.water
        multiplier = simple_damage_multiplier([attack_type], [target_type])
        self.assertEqual(multiplier, 1.0)

        attack_type = self.fire
        target_type = self.aether
        multiplier = simple_damage_multiplier([attack_type], [target_type])
        self.assertEqual(multiplier, 1.0)

    def test_additional_factors(self):
        attack_type = self.fire
        target_type = self.water
        attack_type.lookup_multiplier = MagicMock(return_value=2.0)
        additional_factors = {"boost": 1.5, "nerf": 0.8}
        multiplier = simple_damage_multiplier(
            [attack_type], [target_type], additional_factors
        )
        self.assertEqual(round(multiplier, 1), 2.4)


class TestDamageCalculations(unittest.TestCase):
    def setUp(self):
        self.fire = MagicMock(spec=Element)
        self.fire.name = "fire"
        self.water = MagicMock(spec=Element)
        self.water.name = "water"
        self.grass = MagicMock(spec=Element)
        self.grass.name = "grass"
        self.aether = MagicMock(spec=Element)
        self.aether.name = "aether"
        self.monster = MagicMock(spec=Monster)
        self.monster.types = []
        self.monster.name = ""

    def test_weakest_link1(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.fire]
        self.assertEqual(weakest_link(modifiers, self.monster), 0.5)

    def test_weakest_link2(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        self.monster.types = [self.fire, self.water]
        self.assertEqual(weakest_link(modifiers, self.monster), 0.5)

    def test_weakest_link3(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.water]
        self.assertEqual(weakest_link(modifiers, self.monster), 1.0)

    def test_weakest_link4(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["fire"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(weakest_link(modifiers, self.monster), 0.5)

    def test_strongest_link1(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.fire]
        self.assertEqual(strongest_link(modifiers, self.monster), 0.5)

    def test_strongest_link2(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(strongest_link(modifiers, self.monster), 0.5)

    def test_strongest_link3(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["fire"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(strongest_link(modifiers, self.monster), 0.8)

    def test_strongest_link4(self):
        modifiers = [
            Modifier(attribute="type", values=["water"], multiplier=0.5),
            Modifier(attribute="type", values=["fire"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(strongest_link(modifiers, self.monster), 0.8)

    def test_strongest_link5(self):
        modifiers = [
            Modifier(attribute="type", values=["water"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(strongest_link(modifiers, self.monster), 1.0)

    def test_strongest_link6(self):
        modifiers = []
        self.monster.types = [self.fire]
        self.assertEqual(strongest_link(modifiers, self.monster), 1.0)

    def test_cumulative_damage1(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.fire]
        self.assertEqual(cumulative_damage(modifiers, self.monster), 0.5)

    def test_cumulative_damage2(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        self.monster.types = [self.fire, self.water]
        self.assertEqual(cumulative_damage(modifiers, self.monster), 0.4)

    def test_cumulative_damage3(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.water]
        self.assertEqual(cumulative_damage(modifiers, self.monster), 1.0)

    def test_cumulative_damage4(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["fire"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(cumulative_damage(modifiers, self.monster), 0.4)

    def test_average_damage1(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.fire]
        self.assertEqual(average_damage(modifiers, self.monster), 0.5)

    def test_average_damage2(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        self.monster.types = [self.fire, self.water]
        self.assertEqual(average_damage(modifiers, self.monster), 0.65)

    def test_average_damage3(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.water]
        self.assertEqual(average_damage(modifiers, self.monster), 1.0)

    def test_average_damage4(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["fire"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(average_damage(modifiers, self.monster), 0.65)

    def test_first_applicable_damage1(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.fire]
        self.assertEqual(first_applicable_damage(modifiers, self.monster), 0.5)

    def test_first_applicable_damage2(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        self.monster.types = [self.fire, self.water]
        self.assertEqual(first_applicable_damage(modifiers, self.monster), 0.5)

    def test_first_applicable_damage3(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = [self.water]
        self.assertEqual(first_applicable_damage(modifiers, self.monster), 1.0)

    def test_first_applicable_damage4(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["fire"], multiplier=0.8),
        ]
        self.monster.types = [self.fire]
        self.assertEqual(first_applicable_damage(modifiers, self.monster), 0.5)

    def test_edge_cases1(self):
        modifiers = []
        self.monster.types = [self.fire]
        self.assertEqual(weakest_link(modifiers, self.monster), 1.0)
        self.assertEqual(strongest_link(modifiers, self.monster), 1.0)
        self.assertEqual(cumulative_damage(modifiers, self.monster), 1.0)
        self.assertEqual(average_damage(modifiers, self.monster), 1.0)
        self.assertEqual(first_applicable_damage(modifiers, self.monster), 1.0)

    def test_edge_cases2(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        self.monster.types = []
        self.assertEqual(weakest_link(modifiers, self.monster), 1.0)
        self.assertEqual(strongest_link(modifiers, self.monster), 1.0)
        self.assertEqual(cumulative_damage(modifiers, self.monster), 1.0)
        self.assertEqual(average_damage(modifiers, self.monster), 1.0)
        self.assertEqual(first_applicable_damage(modifiers, self.monster), 1.0)


class TestSimpleDamageCalculate(unittest.TestCase):
    def setUp(self):
        self.mock_technique = MagicMock()
        self.mock_user = MagicMock()
        self.mock_target = MagicMock()

        self.fire = MagicMock(spec=Element)
        self.fire.slug = "fire"
        self.water = MagicMock(spec=Element)
        self.water.slug = "water"

        self.mock_user.level = 10
        self.mock_technique.power = 50

        self.mock_technique.types = [self.fire]
        self.fire.lookup_multiplier = MagicMock(return_value=2.0)

        self.mock_target.types = [self.water]
        self.fire.lookup_multiplier = MagicMock(return_value=2.0)

    def test_valid_melee_damage(self):
        self.mock_technique.range = "melee"
        self.mock_user.melee = 30
        self.mock_target.armour = 20

        damage, multiplier = simple_damage_calculate(
            self.mock_technique, self.mock_user, self.mock_target
        )

        self.assertIsInstance(damage, int)
        self.assertGreater(damage, 0)
        self.assertGreater(multiplier, 0.0)

    def test_valid_touch_damage(self):
        self.mock_technique.range = "touch"
        self.mock_user.melee = 25
        self.mock_target.dodge = 10

        damage, multiplier = simple_damage_calculate(
            self.mock_technique, self.mock_user, self.mock_target
        )

        self.assertGreater(damage, 0)
        self.assertGreater(multiplier, 0.0)

    def test_additional_factors_applied(self):
        self.mock_technique.range = "ranged"
        self.mock_user.ranged = 40
        self.mock_target.dodge = 15

        additional_factors = {"weather_bonus": 0.2}

        damage, multiplier = simple_damage_calculate(
            self.mock_technique,
            self.mock_user,
            self.mock_target,
            additional_factors=additional_factors,
        )

        self.assertGreater(damage, 0)
        self.assertAlmostEqual(multiplier, 0.2, delta=0.2)

    def test_level_based_damage(self):
        self.mock_technique.range = "reliable"
        self.mock_user.level = 15
        self.mock_target.resist = 3

        damage, multiplier = simple_damage_calculate(
            self.mock_technique, self.mock_user, self.mock_target
        )

        self.assertGreater(damage, 0)
        self.assertGreater(multiplier, 0.0)


class TestModifyStat(unittest.TestCase):

    def setUp(self):
        self.monster = MagicMock(spec=Monster)
        self.monster.modifiers = MagicMock()
        self.monster.set_stats = MagicMock()

    def test_add_operation(self):
        self.monster.modifiers.armour = 10
        stat = "armour"
        value = 5.0
        operation = "add"
        expected_value = 15
        modify_stat(self.monster, stat, value, operation)
        self.assertEqual(self.monster.modifiers.armour, expected_value)
        self.monster.set_stats.assert_called_once()

    def test_multiply_operation(self):
        self.monster.armour = 10
        self.monster.modifiers.armour = 0
        stat = "armour"
        value = 1.5
        operation = "multiply"
        expected_value = 15
        modify_stat(self.monster, stat, value, operation)
        self.assertEqual(self.monster.modifiers.armour, expected_value)
        self.monster.set_stats.assert_called_once()

    def test_invalid_operation(self):
        stat = "armour"
        value = 5.0
        operation = "invalid"
        with self.assertRaises(ValueError):
            modify_stat(self.monster, stat, value, operation)

    def test_unrecognized_stat(self):
        stat = "unknown"
        value = 5.0
        operation = "add"
        modify_stat(self.monster, stat, value, operation)
        self.monster.set_stats.assert_not_called()

    def test_modify_stat_calls_set_stats(self):
        self.monster.modifiers.armour = 10
        stat = "armour"
        value = 5.0
        operation = "add"
        modify_stat(self.monster, stat, value, operation)
        self.monster.set_stats.assert_called_once()


class TestSetHealth(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster, hp=100, current_hp=100)
        self.monster.faint = MagicMock()

    def test_set_health_direct(self):
        set_health(self.monster, 50)
        self.assertEqual(self.monster.current_hp, 50)

    def test_set_health_percentage(self):
        set_health(self.monster, 0.5)
        self.assertEqual(self.monster.current_hp, 50)

    def test_adjust_health_add(self):
        set_health(self.monster, 10, adjust=True)
        self.assertEqual(self.monster.current_hp, 100)

    def test_adjust_health_subtract(self):
        set_health(self.monster, -30, adjust=True)
        self.assertEqual(self.monster.current_hp, 70)

    def test_hp_max_limit(self):
        for value in [1.5, 9999]:
            set_health(self.monster, value)
            self.assertEqual(self.monster.current_hp, self.monster.hp)

    def test_faint_triggered_on_zero_hp(self):
        self.monster.faint.reset_mock()
        set_health(self.monster, -200, adjust=True)
        self.assertEqual(self.monster.current_hp, 0)
        self.monster.faint.assert_called_once()

    def test_set_health_to_zero(self):
        set_health(self.monster, 0)
        self.assertEqual(self.monster.current_hp, 0)
        self.monster.faint.assert_called_once()

    def test_hp_min_limit(self):
        for value in [-100, -200]:
            set_health(self.monster, value, adjust=True)
            self.assertEqual(self.monster.current_hp, 0)
            self.monster.faint.assert_called()

    def test_set_health_percentage(self):
        for value in [0.5, 0.25]:
            set_health(self.monster, value)
            self.assertEqual(
                self.monster.current_hp, int(self.monster.hp * value)
            )

    def test_adjust_health_cap(self):
        for value in [50, 200]:
            set_health(self.monster, value, adjust=True)
            self.assertEqual(self.monster.current_hp, self.monster.hp)


class TestChangeBond(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster, bond=50)
        self.minor, self.major = config_monster.bond_range

    def test_increase_bond_direct(self):
        change_bond(self.monster, 10)
        self.assertEqual(self.monster.bond, 60)

    def test_decrease_bond_direct(self):
        change_bond(self.monster, -20)
        self.assertEqual(self.monster.bond, 30)

    def test_increase_bond_percentage(self):
        change_bond(self.monster, 0.2)
        expected_bond = min(self.major, 50 + int(50 * 0.2))
        self.assertEqual(self.monster.bond, expected_bond)

    def test_decrease_bond_percentage(self):
        change_bond(self.monster, -0.5)
        expected_bond = max(self.minor, 50 + int(50 * -0.5))
        self.assertEqual(self.monster.bond, expected_bond)

    def test_bond_does_not_exceed_max(self):
        change_bond(self.monster, 100)
        self.assertEqual(self.monster.bond, self.major)

    def test_bond_does_not_go_below_min(self):
        change_bond(self.monster, -100)
        self.assertEqual(self.monster.bond, self.minor)
