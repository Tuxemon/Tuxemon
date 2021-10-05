import unittest
from unittest import skip
from unittest.mock import Mock

from tuxemon.monster import Monster, MAX_LEVEL


class MonsterTestBase(unittest.TestCase):
    pass


class SetLevel(MonsterTestBase):
    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"
        self.mon.set_level(2)

    def test_set_level(self):
        mon = self.mon
        mon.set_level(5)
        self.assertEqual(mon.level, 5)

    def test_set_level_clamps_max(self):
        mon = self.mon
        mon.set_level(10000)
        self.assertEqual(mon.level, MAX_LEVEL)

    def test_set_level_clamps_to_1(self):
        mon = self.mon
        mon.set_level(-100)
        self.assertEqual(mon.level, 1)
