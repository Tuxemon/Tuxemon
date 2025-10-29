# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.db import CategoryStatus, ResponseStatus
from tuxemon.monster import Monster
from tuxemon.monster_dir.held_item import MonsterItemHandler
from tuxemon.monster_dir.status import MonsterStatusHandler


class TestMonsterStatusHandler(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock()
        self.monster = MagicMock(spec=Monster)
        self.monster.name = "Rockitten"
        self.status = MagicMock(slug="test")
        self.status.host = self.monster
        self.basic = MonsterStatusHandler()
        self.handler = MonsterStatusHandler([self.status])
        self.mock_item = MagicMock()
        self.mock_item.is_immune.return_value = False

    def test_init(self):
        self.assertEqual(self.basic.status, [])

    def test_init_with_status(self):
        self.assertEqual(self.handler.status, [self.status])

    def test_apply_status(self):
        self.monster.held_item = self.mock_item
        self.basic.apply_status(self.session, self.status)
        self.assertEqual(self.basic.status, [self.status])

    def test_apply_status_replace(self):
        status1 = MagicMock(
            category=CategoryStatus.positive,
            on_positive_status=ResponseStatus.replaced,
        )
        status1.host = self.monster
        status2 = MagicMock(on_positive_status=ResponseStatus.replaced)
        status2.host = self.monster
        self.monster.held_item = self.mock_item
        handler = MonsterStatusHandler([status1])
        handler.apply_status(self.session, status2)
        self.assertEqual(len(handler.status), 1)
        self.assertNotEqual(handler.status[0], status1)

    def test_apply_status_remove(self):
        status1 = MagicMock(category=CategoryStatus.positive)
        status1.host = self.monster
        status2 = MagicMock(on_positive_status=ResponseStatus.removed)
        status2.host = self.monster
        self.monster.held_item = self.mock_item
        handler = MonsterStatusHandler([status1])
        handler.apply_status(self.session, status2)
        self.assertEqual(handler.status, [])

    def test_clear_status(self):
        self.handler.clear_status(self.session)
        self.assertEqual(self.handler.status, [])

    def test_get_statuses(self):
        self.assertEqual(self.handler.get_statuses(), [self.status])

    def test_has_status(self):
        self.assertTrue(self.handler.has_status("test"))

    def test_has_status_not(self):
        self.assertFalse(self.handler.has_status("test2"))

    def test_status_exists(self):
        self.assertTrue(self.handler.status_exists())

    def test_status_exists_not(self):
        self.assertFalse(self.basic.status_exists())

    def test_remove_bonded_statuses(self):
        status1 = MagicMock(bond=True)
        status2 = MagicMock(bond=False)
        handler = MonsterStatusHandler([status1, status2])
        handler.remove_bonded_statuses()
        self.assertEqual(len(handler.status), 1)
        self.assertEqual(handler.status[0], status2)
