# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.combat.damage_tracker import DamageTracker
from tuxemon.monster import Monster


class TestDamageTracker(unittest.TestCase):
    def setUp(self):
        self.a = MagicMock(spec=Monster)
        self.b = MagicMock(spec=Monster)
        self.c = MagicMock(spec=Monster)

        self.tracker = DamageTracker()
        # a -> b, 10 damage, turn 1
        self.tracker.log_damage(self.a, self.b, 10, 1)
        # c -> b, 20 damage, turn 2
        self.tracker.log_damage(self.c, self.b, 20, 2)
        # a -> b, 30 damage, turn 3
        self.tracker.log_damage(self.a, self.b, 30, 3)
        # a -> c, 15 damage, turn 1
        self.tracker.log_damage(self.a, self.c, 15, 1)

    def test_log_damage(self):
        damages = self.tracker.get_damages(self.a, self.b)
        self.assertEqual(len(damages), 2)
        self.assertEqual(damages[0].damage, 10)
        self.assertEqual(damages[1].damage, 30)

    def test_get_damages(self):
        damages = self.tracker.get_damages(self.c, self.b)
        self.assertEqual(len(damages), 1)
        self.assertEqual(damages[0].damage, 20)

    def test_get_all_damages(self):
        all_damages = self.tracker.get_all_damages()
        self.assertEqual(len(all_damages), 4)

    def test_remove_monster(self):
        self.tracker.remove_monster(self.b)
        all_damages = self.tracker.get_all_damages()
        self.assertEqual(len(all_damages), 1)
        self.assertEqual(all_damages[0].defense, self.c)  # Only a -> c remains

    def test_clear_damage(self):
        self.tracker.clear_damage()
        all_damages = self.tracker.get_all_damages()
        self.assertEqual(len(all_damages), 0)

    def test_get_attackers(self):
        attackers = self.tracker.get_attackers(self.b)
        self.assertEqual(len(attackers), 2)
        self.assertIn(self.a, attackers)
        self.assertIn(self.c, attackers)

    def test_count_hits(self):
        total_hits, winner_hits = self.tracker.count_hits(self.b, self.a)
        self.assertEqual(total_hits, 3)  # Total hits on b: a -> b, c -> b
        self.assertEqual(winner_hits, 2)  # Hits by a -> b: two instances

    def test_total_damage_by_attacker(self):
        total_damage_a = self.tracker.total_damage_by_attacker(self.a)
        total_damage_c = self.tracker.total_damage_by_attacker(self.c)
        self.assertEqual(total_damage_a, 55)  # a -> b: 10 + 30, a -> c: 15
        self.assertEqual(total_damage_c, 20)  # c -> b: 20
