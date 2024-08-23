# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon import prepare
from tuxemon.monster import Monster
from tuxemon.states.combat.combat_classes import (
    EnqueuedAction,
    get_action_sort_key,
)
from tuxemon.technique.technique import Technique


class TestGetActionSortKey(unittest.TestCase):
    def setUp(self):
        self.monster = Monster()
        self.monster.dodge = 0
        self.monster.speed = 0
        self.tech = Technique()
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
