# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.monster import MonsterItemHandler


class TestMonsterItemHandler(unittest.TestCase):

    def setUp(self):
        self.basic = MonsterItemHandler()
        self.item = MagicMock()
        self.handler = MonsterItemHandler(self.item)

    def test_init(self):
        self.assertIsNone(self.basic.item)

    def test_init_with_item(self):
        self.assertEqual(self.handler.item, self.item)

    def test_set_item(self):
        self.item.behaviors = MagicMock(holdable=True)
        self.basic.set_item(self.item)
        self.assertEqual(self.basic.item, self.item)

    def test_set_item_not_holdable(self):
        self.item.behaviors = MagicMock(holdable=False)
        self.item.name = "Test Item"
        with self.assertLogs(level="ERROR"):
            self.basic.set_item(self.item)
        self.assertIsNone(self.basic.item)

    def test_get_item(self):
        self.assertEqual(self.handler.get_item(), self.item)

    def test_get_item_none(self):
        self.assertIsNone(self.basic.get_item())

    def test_has_item(self):
        self.assertTrue(self.handler.has_item())

    def test_has_item_none(self):
        self.assertFalse(self.basic.has_item())

    def test_clear_item(self):
        self.handler.clear_item()
        self.assertIsNone(self.handler.item)
