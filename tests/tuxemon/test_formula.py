# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import unittest
from unittest.mock import MagicMock, patch

from tuxemon import prepare
from tuxemon.db import Modifier
from tuxemon.element import Element
from tuxemon.formula import (
    average_damage,
    calculate_time_based_multiplier,
    capture,
    cumulative_damage,
    first_applicable_damage,
    set_height,
    set_weight,
    shake_check,
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
    def test_set_weight_zero(self):
        weight = set_weight(0)
        self.assertEqual(weight, 0)

    def test_set_weight_positive(self):
        weight = set_weight(100)
        self.assertGreaterEqual(weight, 100 * 0.9)
        self.assertLessEqual(weight, 100 * 1.1)

    def test_set_weight_negative(self):
        weight = set_weight(-50)
        self.assertGreaterEqual(weight, -50 * 1.1)
        self.assertLessEqual(weight, -50 * 0.9)

    def test_set_weight_randomness(self):
        weights = [set_weight(75) for _ in range(100)]
        self.assertGreaterEqual(len(set(weights)), 1)


class TestSetHeight(unittest.TestCase):
    def test_set_height_zero(self):
        height = set_height(0)
        self.assertEqual(height, 0)

    def test_set_height_positive(self):
        height = set_height(100)
        self.assertGreaterEqual(height, 100 * 0.9)
        self.assertLessEqual(height, 100 * 1.1)

    def test_set_height_negative(self):
        height = set_height(-50)
        self.assertGreaterEqual(height, -50 * 1.1)
        self.assertLessEqual(height, -50 * 0.9)

    def test_set_height_randomness(self):
        heights = [set_height(75) for _ in range(100)]
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


class TestShakeCheck(unittest.TestCase):

    @patch("random.uniform")
    def test_shake_check_basic(self, mock_uniform):
        target = MagicMock(spec=Monster)
        target.hp = 100
        target.current_hp = 50
        target.catch_rate = 100
        target.lower_catch_resistance = 0.9
        target.upper_catch_resistance = 1.1
        mock_uniform.return_value = 1.0
        status_modifier = 1.0
        tuxeball_modifier = 1.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    @patch("random.uniform")
    def test_shake_check_different_values(self, mock_uniform):
        mock_uniform.return_value = 0.5
        target = MagicMock(spec=Monster)
        target.hp = 150
        target.current_hp = 25
        target.catch_rate = 200
        target.lower_catch_resistance = 0.8
        target.upper_catch_resistance = 1.2
        status_modifier = 1.5
        tuxeball_modifier = 2.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)

    @patch("random.uniform")
    def test_shake_check_edge_cases(self, mock_uniform):
        mock_uniform.return_value = 1.0
        target = MagicMock(spec=Monster)
        target.hp = 100
        target.current_hp = 50
        target.catch_rate = 100
        target.lower_catch_resistance = 0.9
        target.upper_catch_resistance = 1.1
        status_modifier = 1.0
        tuxeball_modifier = 1.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)

        target2 = MagicMock(spec=Monster)
        target2.hp = 1000
        target2.current_hp = 1
        target2.catch_rate = 255
        target2.lower_catch_resistance = 1.0
        target2.upper_catch_resistance = 1.0
        result = shake_check(target2, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)

    @patch("random.uniform")
    def test_shake_check_zero_hp(self, mock_uniform):
        mock_uniform.return_value = 1.0
        target = MagicMock(spec=Monster)
        target.hp = 100
        target.current_hp = 0
        target.catch_rate = 100
        target.lower_catch_resistance = 1.0
        target.upper_catch_resistance = 1.0
        status_modifier = 1.0
        tuxeball_modifier = 1.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)


class TestCapture(unittest.TestCase):

    @patch("random.randint")
    def test_capture_success(self, mock_randint):
        mock_randint.return_value = prepare.MAX_SHAKE_RATE // 2
        shake_check = prepare.MAX_SHAKE_RATE
        captured, shakes = capture(shake_check)
        self.assertTrue(captured)
        self.assertEqual(shakes, prepare.TOTAL_SHAKES)

    @patch("random.randint")
    def test_capture_failure_first_shake(self, mock_randint):
        mock_randint.return_value = prepare.MAX_SHAKE_RATE
        shake_check = 0
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, 1)

    @patch("random.randint")
    def test_capture_failure_middle_shake(self, mock_randint):
        mock_randint.side_effect = [
            prepare.MAX_SHAKE_RATE // 4,
            prepare.MAX_SHAKE_RATE // 4,
            prepare.MAX_SHAKE_RATE,
        ]
        shake_check = prepare.MAX_SHAKE_RATE // 4
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, 3)

    @patch("random.randint")
    def test_capture_failure_last_shake(self, mock_randint):
        mock_randint.side_effect = [
            prepare.MAX_SHAKE_RATE // 4,
            prepare.MAX_SHAKE_RATE // 4,
            prepare.MAX_SHAKE_RATE // 4,
            prepare.MAX_SHAKE_RATE,
        ]
        shake_check = prepare.MAX_SHAKE_RATE // 4
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, prepare.TOTAL_SHAKES)

    @patch("random.randint")
    def test_capture_edge_case_shake_check_zero(self, mock_randint):
        mock_randint.return_value = prepare.MAX_SHAKE_RATE // 2
        shake_check = 0
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, 1)

    @patch("random.randint")
    def test_capture_edge_case_shake_check_max(self, mock_randint):
        mock_randint.return_value = prepare.MAX_SHAKE_RATE // 2
        shake_check = prepare.MAX_SHAKE_RATE
        captured, shakes = capture(shake_check)
        self.assertTrue(captured)
        self.assertEqual(shakes, prepare.TOTAL_SHAKES)


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
