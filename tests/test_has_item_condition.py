import os
import sys
import unittest

# for some test runners that cannot find the tuxemon core
sys.path.insert(0, os.path.join('tuxemon', ))
from collections import namedtuple
from core.control import HeadlessControl
from core.components.event.conditions.has_item import HasItemCondition

# mocks
cond_nt = namedtuple("condition", ("parameters",))
npc_nt = namedtuple("npc", ("inventory",))


class HasItemConditionTest(unittest.TestCase):
    def make_test(self, parameters, inventory):
        game = HeadlessControl()
        condition = cond_nt(parameters)
        player = npc_nt(inventory)
        game.player1 = player
        test = HasItemCondition()
        return test.test(game, condition)

    def test_empty(self):
        parameters = ('player', 'item_potion')
        inventory = {}
        result = self.make_test(parameters, inventory)
        self.assertFalse(result)

    def test_has(self):
        parameters = ('player', 'item_potion')
        inventory = {'item_potion': {'quantity': 1}}
        result = self.make_test(parameters, inventory)
        self.assertTrue(result)

    def test_has_zero(self):
        parameters = ('player', 'item_potion')
        inventory = {'item_potion': {'quantity': 0}}
        result = self.make_test(parameters, inventory)
        self.assertFalse(result)

    def test_eq(self):
        parameters = ('player', 'item_potion', 'equals')
        inventory = {'item_potion': {'quantity': 0}}
        result = self.make_test(parameters, inventory)
        self.assertTrue(result)

    def test_lt(self):
        parameters = ('player', 'item_potion', 'less_than', 10)
        inventory = {'item_potion': {'quantity': 5}}
        result = self.make_test(parameters, inventory)
        self.assertTrue(result)

    def test_gt(self):
        parameters = ('player', 'item_potion', 'greater_than', 10)
        inventory = {'item_potion': {'quantity': 5}}
        result = self.make_test(parameters, inventory)
        self.assertFalse(result)

    def test_valid_q(self):
        parameters = ('player', 'item_potion', 'greater_than', -1)
        inventory = {'item_potion': {'quantity': 5}}
        with self.assertRaises(ValueError):
            self.make_test(parameters, inventory)
