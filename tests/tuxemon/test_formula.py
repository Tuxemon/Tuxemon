# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import unittest

from tuxemon import prepare
from tuxemon.formula import (
    calculate_time_based_multiplier,
    set_height,
    set_weight,
    simple_heal,
    update_stat,
)


class MockMonster1:
    def __init__(self, melee, ranged, dodge, taste_warm, taste_cold) -> None:
        self.melee = melee
        self.ranged = ranged
        self.dodge = dodge
        self.taste_warm = taste_warm
        self.taste_cold = taste_cold


class TestUpdateStat(unittest.TestCase):
    def setUp(self):
        self.monster = MockMonster1(
            melee=10,
            ranged=10,
            dodge=10,
            taste_warm="salty",
            taste_cold="flakey",
        )

    def test_update_stat_matching_taste_bonus(self):
        bonus = update_stat(self.monster, "melee")
        self.assertEqual(bonus, 1)

    def test_update_stat_matching_taste_malus(self):
        malus = update_stat(self.monster, "ranged")
        self.assertEqual(malus, -1)

    def test_update_stat_matching_taste_neuter(self):
        neuter = update_stat(self.monster, "dodge")
        self.assertEqual(neuter, 0)


class MockTechnique1:
    def __init__(self, healing_power: float) -> None:
        self.healing_power = healing_power


class MockMonster2:
    def __init__(self, level: int) -> None:
        self.level = level


class TestSimpleHeal(unittest.TestCase):
    def test_simple_heal_no_factors(self):
        technique = MockTechnique1(5)
        monster = MockMonster2(10)
        expected_heal = (
            prepare.COEFF_DAMAGE + monster.level * technique.healing_power
        )
        actual_heal = simple_heal(technique, monster)
        self.assertEqual(int(expected_heal), actual_heal)

    def test_simple_heal_with_factors(self):
        technique = MockTechnique1(3)
        monster = MockMonster2(15)
        factors = {"boost": 1.2, "penalty": 0.8}
        expected_multiplier = math.prod(factors.values())
        expected_heal = (
            prepare.COEFF_DAMAGE + monster.level * technique.healing_power
        ) * expected_multiplier
        actual_heal = simple_heal(technique, monster, factors)
        self.assertEqual(int(expected_heal), actual_heal)

    def test_simple_heal_empty_factors(self):
        technique = MockTechnique1(2)
        monster = MockMonster2(20)
        factors = {}
        expected_heal = (
            prepare.COEFF_DAMAGE + monster.level * technique.healing_power
        )
        actual_heal = simple_heal(technique, monster, factors)
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
