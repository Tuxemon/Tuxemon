import os
import sys
import unittest
from collections import namedtuple
from nose.tools import nottest

# for some test runners that cannot find the tuxemon core
sys.path.insert(0, os.path.join('tuxemon', ))
from tuxemon.core.control import HeadlessControl
from tuxemon.core.components.event.conditions.has_item import HasItemCondition

# mocks and defaults
cond_nt = namedtuple("condition", ("parameters",))
npc_nt = namedtuple("npc", ("inventory",))
test_item = 'item_potion'
test_target = 'player'


def inventory(n):
    return {test_item: {'quantity': n}}


@nottest
def make_test(parameters, inventory):
    game = HeadlessControl()
    condition = cond_nt(parameters)
    player = npc_nt(inventory)
    game.player1 = player
    test = HasItemCondition()
    return test.test(game, condition)


@nottest
def test_op(op):
    parameters = (test_target, test_item, op, 1)
    eq = make_test(parameters, inventory(1))
    parameters = (test_target, test_item, op, 0)
    gt = make_test(parameters, inventory(1))
    parameters = (test_target, test_item, op, 1)
    lt = make_test(parameters, inventory(0))
    return eq, gt, lt


class HasItemConditionTest(unittest.TestCase):
    def test_short_form_one(self):
        parameters = (test_target, test_item)
        self.assertTrue(make_test(parameters, inventory(1)))

    def test_short_form_many(self):
        parameters = (test_target, test_item)
        self.assertTrue(make_test(parameters, inventory(2)))

    def test_short_form_zero_quantity(self):
        parameters = (test_target, test_item)
        self.assertFalse(make_test(parameters, inventory(0)))

    def test_short_form_not_in_inventory(self):
        parameters = (test_target, test_item)
        self.assertFalse(make_test(parameters, dict()))

    def test_valid_quantity(self):
        parameters = (test_target, test_item, 'equals', -1)
        with self.assertRaises(ValueError):
            make_test(parameters, dict())

    def test_invalid_operator(self):
        parameters = (test_target, test_item, 'no', 1)
        with self.assertRaises(ValueError):
            make_test(parameters, dict())

    def test_missing_operator_string(self):
        parameters = (test_target, test_item, '', 0)
        self.assertTrue(make_test(parameters, dict()))

    def test_missing_operator_None(self):
        parameters = (test_target, test_item, None, 1)
        self.assertTrue(make_test(parameters, inventory(2)))

    def test_mixed_case(self):
        parameters = (test_target, test_item, 'EquaLS', 0)
        self.assertTrue(make_test(parameters, dict()))

    def test_comps(self):
        self.assertEqual(test_op('equals'), (1, 0, 0))
        self.assertEqual(test_op('greater_or_equal'), (1, 1, 0))
        self.assertEqual(test_op('less_or_equal'), (1, 0, 1))
        self.assertEqual(test_op('greater_than'), (0, 1, 0))
        self.assertEqual(test_op('less_than'), (0, 0, 1))
