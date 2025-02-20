# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon import prepare
from tuxemon.formula import speed_monster
from tuxemon.monster import Monster
from tuxemon.states.combat.combat_classes import (
    EnqueuedAction,
    get_action_sort_key,
)
from tuxemon.technique.technique import Technique


class TestGetActionSortKey(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster)
        self.monster.speed = 10.0
        self.monster.dodge = 5.0
        self.tech = MagicMock(spec=Technique)
        self.tech.is_fast = False
        self.tech.sort = "damage"

    def test_none_method(self):
        action = EnqueuedAction(user=None, method=None, target=None)
        self.assertEqual(get_action_sort_key(action), (0, 0))

    def test_none_user(self):
        action = EnqueuedAction(user=None, method=self.tech, target=None)
        self.assertEqual(get_action_sort_key(action), (0, 0))

    def test_meta_action(self):
        self.tech.sort = "meta"
        action = EnqueuedAction(user=None, method=self.tech, target=None)
        self.assertEqual(
            get_action_sort_key(action), (prepare.SORT_ORDER.index("meta"), 0)
        )

    def test_potion_action(self):
        self.tech.sort = "potion"
        action = EnqueuedAction(user=None, method=self.tech, target=None)
        self.assertEqual(
            get_action_sort_key(action),
            (prepare.SORT_ORDER.index("potion"), 0),
        )

    def test_damage_action(self):
        self.tech.sort = "damage"
        action = EnqueuedAction(
            user=self.monster, method=self.tech, target=None
        )
        self.assertGreaterEqual(
            get_action_sort_key(action),
            (prepare.SORT_ORDER.index("potion"), 0),
        )


class TestSpeedTestFunction(unittest.TestCase):

    def setUp(self):
        self.monster = MagicMock(spec=Monster)
        self.monster.speed = 10.0
        self.monster.dodge = 5.0

        self.monster1 = MagicMock(spec=Monster)
        self.monster1.speed = 10.0
        self.monster1.dodge = 5.0

        self.monster2 = MagicMock(spec=Monster)
        self.monster2.speed = 15.0
        self.monster2.dodge = 3.0

    def test_speed_modifier_fast_technique(self):
        technique = MagicMock(spec=Technique)
        technique.is_fast = True
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)
        self.assertLessEqual(
            max(results),
            self.monster.speed * prepare.MULTIPLIER_SPEED
            + self.monster.dodge * 0.01
            + prepare.SPEED_OFFSET,
        )

    def test_speed_modifier_normal_technique(self):
        technique = MagicMock(spec=Technique)
        technique.is_fast = False
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)
        self.assertLessEqual(
            max(results),
            self.monster.speed
            + self.monster.dodge * 0.01
            + prepare.SPEED_OFFSET,
        )

    def test_speed_modifier_with_random_offset(self):
        technique = MagicMock(spec=Technique)
        technique.is_fast = True
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)
        self.assertLessEqual(
            max(results),
            self.monster.speed * prepare.MULTIPLIER_SPEED
            + self.monster.dodge * 0.01
            + prepare.SPEED_OFFSET,
        )

    def test_speed_modifier_with_dodge(self):
        technique = MagicMock(spec=Technique)
        technique.is_fast = False
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        expected_dodge_contribution = self.monster.dodge * 0.01
        self.assertGreaterEqual(
            min(results),
            self.monster.speed
            + expected_dodge_contribution
            - prepare.SPEED_OFFSET,
        )
        self.assertLessEqual(
            max(results),
            self.monster.speed
            + expected_dodge_contribution
            + prepare.SPEED_OFFSET,
        )

    def test_zero_speed(self):
        self.monster.speed = 0.0
        technique = MagicMock(spec=Technique)
        technique.is_fast = True
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)

    def test_negative_speed(self):
        self.monster.speed = -5.0
        technique = MagicMock(spec=Technique)
        technique.is_fast = True
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)

    def test_zero_dodge(self):
        self.monster.dodge = 0.0
        technique = MagicMock(spec=Technique)
        technique.is_fast = False
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)
        self.assertLessEqual(
            max(results), self.monster.speed + prepare.SPEED_OFFSET
        )

    def test_high_values(self):
        self.monster.speed = 1e6
        self.monster.dodge = 1e6
        technique = MagicMock(spec=Technique)
        technique.is_fast = True
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)
        self.assertLessEqual(
            max(results),
            self.monster.speed * prepare.MULTIPLIER_SPEED
            + self.monster.dodge * 0.01
            + prepare.SPEED_OFFSET,
        )

    def test_randomness_effect(self):
        technique = MagicMock(spec=Technique)
        technique.is_fast = True
        results = [speed_monster(self.monster, technique) for _ in range(1000)]
        self.assertGreaterEqual(min(results), 1)
        self.assertLessEqual(
            max(results),
            self.monster.speed * prepare.MULTIPLIER_SPEED
            + self.monster.dodge * 0.01
            + prepare.SPEED_OFFSET,
        )

    def test_speed_comparison_between_monsters(self):
        technique = MagicMock(spec=Technique)
        technique.is_fast = True

        results1 = [
            speed_monster(self.monster1, technique) for _ in range(1000)
        ]
        results2 = [
            speed_monster(self.monster2, technique) for _ in range(1000)
        ]

        with self.subTest("Comparing speed modifiers"):
            self.assertGreaterEqual(min(results1), 1)
            self.assertGreaterEqual(min(results2), 1)
            self.assertLessEqual(
                max(results1),
                self.monster1.speed * prepare.MULTIPLIER_SPEED
                + self.monster1.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )
            self.assertLessEqual(
                max(results2),
                self.monster2.speed * prepare.MULTIPLIER_SPEED
                + self.monster2.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )

            self.assertLessEqual(
                sum(results1) / len(results1), sum(results2) / len(results2)
            )

    def test_speed_with_different_speed_values(self):
        monster3 = MagicMock(spec=Monster)
        monster3.speed = 20.0
        monster3.dodge = 5.0

        technique = MagicMock(spec=Technique)
        technique.is_fast = True

        results1 = [
            speed_monster(self.monster1, technique) for _ in range(1000)
        ]
        results3 = [speed_monster(monster3, technique) for _ in range(1000)]

        with self.subTest("Comparing different speed values"):
            self.assertGreaterEqual(min(results1), 1)
            self.assertGreaterEqual(min(results3), 1)
            self.assertLessEqual(
                max(results1),
                self.monster1.speed * prepare.MULTIPLIER_SPEED
                + self.monster1.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )
            self.assertLessEqual(
                max(results3),
                monster3.speed * prepare.MULTIPLIER_SPEED
                + monster3.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )

            self.assertGreater(
                sum(results3) / len(results3), sum(results1) / len(results1)
            )

    def test_speed_with_different_dodge_values(self):
        monster4 = MagicMock(spec=Monster)
        monster4.speed = 10.0
        monster4.dodge = 10.0

        technique = MagicMock(spec=Technique)
        technique.is_fast = True

        results1 = [
            speed_monster(self.monster1, technique) for _ in range(10000)
        ]
        results4 = [speed_monster(monster4, technique) for _ in range(10000)]

        with self.subTest("Comparing different dodge values"):
            self.assertGreaterEqual(min(results1), 1)
            self.assertGreaterEqual(min(results4), 1)
            self.assertLessEqual(
                max(results1),
                self.monster1.speed * prepare.MULTIPLIER_SPEED
                + self.monster1.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )
            self.assertLessEqual(
                max(results4),
                monster4.speed * prepare.MULTIPLIER_SPEED
                + monster4.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )

            self.assertGreater(
                sum(results4) / len(results4),
                sum(results1) / len(results1) * 0.9,
            )

    def test_extreme_speed_and_dodge_values(self):
        monster5 = MagicMock(spec=Monster)
        monster5.speed = 1e6
        monster5.dodge = 1.0

        technique = MagicMock(spec=Technique)
        technique.is_fast = True

        results1 = [
            speed_monster(self.monster1, technique) for _ in range(1000)
        ]
        results5 = [speed_monster(monster5, technique) for _ in range(1000)]

        with self.subTest("Comparing extreme speed and dodge values"):
            self.assertGreaterEqual(min(results1), 1)
            self.assertGreaterEqual(min(results5), 1)
            self.assertLessEqual(
                max(results1),
                self.monster1.speed * prepare.MULTIPLIER_SPEED
                + self.monster1.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )
            self.assertLessEqual(
                max(results5),
                monster5.speed * prepare.MULTIPLIER_SPEED
                + monster5.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )

            self.assertGreater(
                sum(results5) / len(results5), sum(results1) / len(results1)
            )

    def test_equal_speed_and_dodge(self):
        monster6 = MagicMock(spec=Monster)
        monster6.speed = 10.0
        monster6.dodge = 5.0

        technique = MagicMock(spec=Technique)
        technique.is_fast = True

        results1 = [
            speed_monster(self.monster1, technique) for _ in range(1000)
        ]
        results6 = [speed_monster(monster6, technique) for _ in range(1000)]

        with self.subTest("Comparing equal speed and dodge"):
            self.assertGreaterEqual(min(results1), 1)
            self.assertGreaterEqual(min(results6), 1)
            self.assertLessEqual(
                max(results1),
                self.monster1.speed * prepare.MULTIPLIER_SPEED
                + self.monster1.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )
            self.assertLessEqual(
                max(results6),
                monster6.speed * prepare.MULTIPLIER_SPEED
                + monster6.dodge * 0.01
                + prepare.SPEED_OFFSET,
            )

            self.assertLess(
                abs(
                    sum(results6) / len(results6)
                    - sum(results1) / len(results1)
                ),
                5,
            )

    def test_fast_vs_normal_technique(self):
        technique_fast = MagicMock(spec=Technique)
        technique_fast.is_fast = True
        results1_fast = [
            speed_monster(self.monster1, technique_fast) for _ in range(1000)
        ]

        technique_normal1 = MagicMock(spec=Technique)
        technique_normal1.is_fast = False
        results1_normal = [
            speed_monster(self.monster1, technique_normal1)
            for _ in range(1000)
        ]

        results2_fast = [
            speed_monster(self.monster2, technique_fast) for _ in range(1000)
        ]

        results2_normal = [
            speed_monster(self.monster2, technique_normal1)
            for _ in range(1000)
        ]

        with self.subTest("Comparing fast vs normal technique for monster1"):
            self.assertGreater(
                sum(results1_fast) / len(results1_fast),
                sum(results1_normal) / len(results1_normal),
            )

        with self.subTest("Comparing fast vs normal technique for monster2"):
            self.assertGreater(
                sum(results2_fast) / len(results2_fast),
                sum(results2_normal) / len(results2_normal),
            )
