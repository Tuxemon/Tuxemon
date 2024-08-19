# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import sys
import unittest
from typing import Literal, Optional, Union
from unittest import mock

from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.tools import (
    cast_value,
    compare,
    copy_dict_with_keys,
    number_or_variable,
    round_to_divisible,
)


def mockPlayer(self) -> None:
    self.game_variables = {"my_var": 2}


def mockSession(self) -> None:
    self.session = local_session


class TestRoundToDivisible(unittest.TestCase):
    def test_round_down(self):
        result = round_to_divisible(1, 16)
        self.assertEqual(result, 0)

    def test_round_up(self):
        result = round_to_divisible(15, 16)
        self.assertEqual(result, 16)

    def test_round_up_if_half(self):
        result = round_to_divisible(24, 16)
        self.assertEqual(result, 32)

    def test_alternate_divisor(self):
        result = round_to_divisible(51, 100)
        self.assertEqual(result, 100)

    def test_return_type_is_int(self):
        result = type(round_to_divisible(0))
        self.assertEqual(result, int)


class TestCopyDictWithKeys(unittest.TestCase):
    def test(self):
        source = {"a": 1, "b": 2, "c": 3}
        keys = ["a", "c"]
        expected = {"a": 1, "c": 3}
        result = copy_dict_with_keys(source, keys)
        self.assertEqual(result, expected)


class TestVariableNumber(unittest.TestCase):
    def test_var(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            # session = Session()
            player = Player()
            local_session.player = player

            result = number_or_variable(local_session, "1")
            self.assertEqual(result, 1.0)

            result = number_or_variable(local_session, "1.5")
            print(result)
            self.assertEqual(result, 1.5)

            with self.assertRaises(ValueError):
                result = number_or_variable(local_session, "unbound_var")

            result = number_or_variable(local_session, "my_var")
            self.assertEqual(result, 2.0)


class TestCastValue(unittest.TestCase):
    def test_basic_types(self):
        self.assertEqual(cast_value(((int, "param"), 42)), 42)
        self.assertEqual(cast_value(((str, "param"), "hello")), "hello")
        self.assertEqual(cast_value(((float, "param"), 3.14)), 3.14)
        self.assertEqual(cast_value(((bool, "param"), True)), True)

    def test_none_handling(self):
        self.assertEqual(cast_value(((None, "param"), None)), None)
        with self.assertRaises(ValueError):
            cast_value(((int, None), None))
        self.assertEqual(cast_value(((str, None), None)), "None")

    def test_literal_types(self):
        with self.assertRaises(TypeError):
            cast_value(((Literal[1, 2, 3], "param"), 4))

    def test_union_types(self):
        if sys.version_info >= (3, 10):
            self.assertEqual(
                cast_value(((Union[int, str], "param"), 123)), 123
            )
            self.assertEqual(
                cast_value(((Union[int, str], "param"), "abc")), "abc"
            )
            with self.assertRaises(ValueError):
                cast_value(((Union[int, bool], "param"), "abc"))
        else:
            self.skipTest("This test requires Python 3.10 or later")

    def test_int_float_priority(self):
        with self.assertRaises(ValueError):
            cast_value(((int, float, "param"), 42))
        with self.assertRaises(ValueError):
            cast_value(((float, int, "param"), 3.14))

    def test_def_error_handling(self):
        self.assertEqual(cast_value(((str, "param"), 123)), "123")
        with self.assertRaises(ValueError):
            cast_value(((int, "param"), "abc"))

    def test_sequence_of_types_combinations(self):
        with self.assertRaises(ValueError):
            cast_value(((int, str, bool), True))

    def test_optional_types_and_sequences(self):
        if sys.version_info >= (3, 10):
            self.assertEqual(cast_value(((Optional[int], str), None)), None)
            with self.assertRaises(ValueError):
                cast_value(((Optional[int], None, str), True))
        else:
            self.skipTest("This test requires Python 3.10 or later")

    def test_edge_cases_with_sequences(self):
        with self.assertRaises(ValueError):
            cast_value((([], "param"), 42))
        with self.assertRaises(ValueError):
            cast_value(((None, None, "param"), None))


class TestCompare(unittest.TestCase):
    def test_less_than(self):
        self.assertTrue(compare("<", 2, 3))
        self.assertFalse(compare("<", 3, 2))

    def test_less_or_equal(self):
        self.assertTrue(compare("<=", 2, 3))
        self.assertTrue(compare("<=", 2, 2))
        self.assertFalse(compare("<=", 3, 2))

    def test_greater_than(self):
        self.assertTrue(compare(">", 3, 2))
        self.assertFalse(compare(">", 2, 3))

    def test_greater_or_equal(self):
        self.assertTrue(compare(">=", 3, 2))
        self.assertTrue(compare(">=", 2, 2))
        self.assertFalse(compare(">=", 2, 3))

    def test_equals(self):
        self.assertTrue(compare("==", 2, 2))
        self.assertFalse(compare("==", 3, 2))

    def test_not_equals(self):
        self.assertTrue(compare("!=", 2, 3))
        self.assertFalse(compare("!=", 2, 2))

    def test_invalid_operator(self):
        with self.assertRaises(ValueError):
            compare("invalid", 2, 3)

    def test_float_values(self):
        self.assertTrue(compare("<", 2.5, 3.0))
        self.assertTrue(compare(">=", 3.0, 2.5))

    def test_zero_values(self):
        self.assertTrue(compare("==", 0, 0))
        self.assertFalse(compare("!=", 0, 0))
        self.assertTrue(compare(">=", 0, -1))
        self.assertTrue(compare("<=", 0, 1))

    def test_infinity(self):
        self.assertTrue(compare(">", math.inf, 5))
        self.assertTrue(compare("<", -math.inf, 5))

    def test_nan(self):
        self.assertFalse(compare("==", math.nan, math.nan))
        self.assertTrue(compare("!=", math.nan, math.nan))

    def test_int_and_float(self):
        self.assertTrue(compare("==", 2, 2.0))
        self.assertTrue(compare("<", 2.5, 3))

    def test_invalid_data_types(self):
        with self.assertRaises(TypeError):
            compare("<", "a", 5)
        with self.assertRaises(TypeError):
            compare(">", 3, "b")
