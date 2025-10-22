# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import sys
import unittest
from typing import Literal, Optional, Union
from unittest.mock import MagicMock

from tuxemon.player import Player
from tuxemon.tools import (
    cast_value,
    check_condition,
    compare,
    copy_dict_with_keys,
    number_or_variable,
    parse_flag,
    round_to_divisible,
)


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
    def setUp(self):
        self.player = MagicMock(spec=Player)
        self.player.game_variables = {
            "my_var": 2,
            "non_numeric": "text",
            "none_value": None,
        }

    def test_numeric_string(self):
        result = number_or_variable(self.player.game_variables, "1")
        self.assertEqual(result, 1.0)

        result = number_or_variable(self.player.game_variables, "1.5")
        self.assertEqual(result, 1.5)

    def test_variable_name(self):
        result = number_or_variable(self.player.game_variables, "my_var")
        self.assertEqual(result, 2.0)

    def test_unbound_variable(self):
        with self.assertRaises(ValueError):
            number_or_variable(self.player.game_variables, "unbound_var")

    def test_invalid_numeric_string(self):
        with self.assertRaises(ValueError):
            number_or_variable(self.player.game_variables, "1.5.3")

        with self.assertRaises(ValueError):
            number_or_variable(self.player.game_variables, "-1..5")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            number_or_variable(self.player.game_variables, "")

    def test_negative_number(self):
        result = number_or_variable(self.player.game_variables, "-10")
        self.assertEqual(result, -10.0)

    def test_zero(self):
        result = number_or_variable(self.player.game_variables, "0")
        self.assertEqual(result, 0.0)

    def test_scientific_notation(self):
        result = number_or_variable(self.player.game_variables, "1e3")
        self.assertEqual(result, 1000.0)

    def test_non_numeric_variable(self):
        with self.assertRaises(ValueError):
            number_or_variable(self.player.game_variables, "non_numeric")

    def test_none_variable(self):
        with self.assertRaises(ValueError):
            number_or_variable(self.player.game_variables, "none_value")


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
        self.assertEqual(cast_value(((Union[int, str], "param"), 123)), 123)
        self.assertEqual(
            cast_value(((Union[int, str], "param"), "abc")), "abc"
        )
        with self.assertRaises(ValueError):
            cast_value(((Union[int, bool], "param"), "abc"))

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
        self.assertEqual(cast_value(((Optional[int], str), None)), None)
        with self.assertRaises(ValueError):
            cast_value(((Optional[int], None, str), True))

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


class TestParseFlag(unittest.TestCase):

    def test_parse_flag_truthy(self):
        self.assertTrue(parse_flag("true"))
        self.assertTrue(parse_flag("True"))
        self.assertTrue(parse_flag("1"))
        self.assertTrue(parse_flag("yes"))
        self.assertTrue(parse_flag("YeS"))

    def test_parse_flag_falsy(self):
        self.assertFalse(parse_flag("false"))
        self.assertFalse(parse_flag("0"))
        self.assertFalse(parse_flag("no"))
        self.assertFalse(parse_flag(""))
        self.assertFalse(parse_flag(None))
        self.assertFalse(parse_flag("maybe"))

    def test_parse_flag_edge_cases(self):
        self.assertTrue(parse_flag("  yes  "))
        self.assertFalse(parse_flag("  no  "))
        self.assertFalse(parse_flag("YES!"))
        self.assertFalse(parse_flag("truEly"))
        self.assertFalse(parse_flag("2"))
        self.assertFalse(parse_flag("-1"))


class TestCheckCondition(unittest.TestCase):
    def test_check_condition_positive(self):
        dataset = {"fire", "water", "earth"}
        self.assertTrue(check_condition("fire", dataset))
        self.assertTrue(check_condition("Water", dataset))
        self.assertFalse(check_condition("air", dataset))

    def test_check_condition_negative(self):
        dataset = {"fire", "water", "earth"}
        self.assertTrue(check_condition("!air", dataset))
        self.assertFalse(check_condition("!fire", dataset))

    def test_check_condition_empty(self):
        dataset = {"fire"}
        self.assertFalse(check_condition("", dataset))
        self.assertFalse(check_condition("   ", dataset))

    def test_check_condition_edge_cases(self):
        dataset = {"fire", "water"}
        self.assertTrue(check_condition("  fire  ", dataset))
        self.assertTrue(check_condition("!  earth  ", dataset))
        self.assertTrue(check_condition("!!fire", dataset))
        empty_set = set()
        self.assertFalse(check_condition("fire", empty_set))
        self.assertTrue(check_condition("!fire", empty_set))
        self.assertTrue(check_condition("!", dataset))
        self.assertFalse(check_condition("   ", dataset))
