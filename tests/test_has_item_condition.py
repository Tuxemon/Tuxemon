import os
import sys
import unittest
from collections import namedtuple

# for some test runners that cannot find the tuxemon core
sys.path.insert(0, os.path.join('tuxemon', ))
from core.control import HeadlessControl
from core.components.event.conditions.has_item import HasItemCondition

# mocks
cond_nt = namedtuple("condition", ("parameters",))
npc_nt = namedtuple("npc", ("inventory",))

test_item = 'item_potion'
test_target = 'player'


def make_test(parameters, inventory):
    game = HeadlessControl()
    condition = cond_nt(parameters)
    player = npc_nt(inventory)
    game.player1 = player
    test = HasItemCondition()
    return test.test(game, condition)


def test_op(op):
    def test_eq():
        parameters = (test_target, test_item, op, 1)
        inventory = {test_item: {'quantity': 1}}
        return make_test(parameters, inventory)

    def test_gt():
        parameters = (test_target, test_item, op, 0)
        inventory = {test_item: {'quantity': 1}}
        return make_test(parameters, inventory)

    def test_lt():
        parameters = (test_target, test_item, op, 1)
        inventory = {test_item: {'quantity': 0}}
        return make_test(parameters, inventory)

    return test_eq(), test_gt(), test_lt()


class HasItemConditionTest(unittest.TestCase):
    def test_has(self):
        # short form of condition
        parameters = (test_target, test_item)
        inventory = {test_item: {'quantity': 1}}
        result = make_test(parameters, inventory)
        self.assertTrue(result)

        # also works when quantity is greater than the condition specifies
        parameters = (test_target, test_item)
        inventory = {test_item: {'quantity': 2}}
        result = make_test(parameters, inventory)
        self.assertTrue(result)

    def test_has_zero(self):
        # 0 inventory
        parameters = (test_target, test_item)
        inventory = {test_item: {'quantity': 0}}
        result = make_test(parameters, inventory)
        self.assertFalse(result)

    def test_no_inventory(self):
        # not in inventory
        parameters = (test_target, test_item)
        inventory = {}
        result = make_test(parameters, inventory)
        self.assertFalse(result)

    def test_valid_q(self):
        # quantity must be 0 or more
        parameters = (test_target, test_item, 'equals', -1)
        inventory = {test_item: {'quantity': 5}}
        with self.assertRaises(ValueError):
            make_test(parameters, inventory)

    def test_valid_op(self):
        # invalid operator
        parameters = (test_target, test_item, 'no', 1)
        inventory = {}
        with self.assertRaises(ValueError):
            make_test(parameters, inventory)

    def test_missing_op(self):
        # invalid operator
        parameters = (test_target, test_item, '', 0)
        inventory = {}
        result = make_test(parameters, inventory)
        self.assertTrue(result)

        parameters = (test_target, test_item, None, 1)
        inventory = {test_item: {'quantity': 2}}
        result = make_test(parameters, inventory)
        self.assertTrue(result)

    def test_eq(self):
        eq, gt, lt = test_op('equals')
        self.assertTrue(eq)
        self.assertFalse(gt)
        self.assertFalse(lt)

    def test_ge(self):
        eq, gt, lt = test_op('greater_or_equal')
        self.assertTrue(eq)
        self.assertTrue(gt)
        self.assertFalse(lt)

    def test_le(self):
        eq, gt, lt = test_op('less_or_equal')
        self.assertTrue(eq)
        self.assertFalse(gt)
        self.assertTrue(lt)

    def test_gt(self):
        eq, gt, lt = test_op('greater_than')
        self.assertFalse(eq)
        self.assertTrue(gt)
        self.assertFalse(lt)

    def test_lt(self):
        eq, gt, lt = test_op('less_than')
        self.assertFalse(eq)
        self.assertFalse(gt)
        self.assertTrue(lt)
