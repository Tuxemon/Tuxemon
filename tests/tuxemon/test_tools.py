# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
import unittest
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Literal, Optional, Union
from unittest.mock import MagicMock
from uuid import UUID

from tuxemon.math import Vector2
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
        # int from int
        self.assertEqual(cast_value(((int, "param"), 42)), 42)
        # int from string
        self.assertEqual(cast_value(((int, "param"), "42")), 42)
        # int from float string
        self.assertEqual(cast_value(((int, "param"), "3.0")), 3)
        # float from float
        self.assertEqual(cast_value(((float, "param"), 3.14)), 3.14)
        # float from int string
        self.assertEqual(cast_value(((float, "param"), "42")), 42.0)
        # str from str
        self.assertEqual(cast_value(((str, "param"), "hello")), "hello")
        # str from int
        self.assertEqual(cast_value(((str, "param"), 123)), "123")
        # bool from bool
        self.assertEqual(cast_value(((bool, "param"), True)), True)
        self.assertEqual(cast_value(((bool, "param"), False)), False)
        # bool from string
        self.assertTrue(cast_value(((bool, "param"), "true")))
        self.assertFalse(cast_value(((bool, "param"), "false")))
        self.assertTrue(cast_value(((bool, "param"), "yes")))
        self.assertFalse(cast_value(((bool, "param"), "no")))
        self.assertTrue(cast_value(((bool, "param"), "1")))
        self.assertFalse(cast_value(((bool, "param"), "0")))

    def test_none_handling(self):
        with self.assertRaises(ValueError):
            cast_value(((str, "param"), None))

    def test_literal_types(self):
        with self.assertRaises(ValueError):
            cast_value(((Literal[1, 2, 3], "param"), 4))

    def test_union_types(self):
        self.assertEqual(cast_value(((Union[int, str], "param"), 123)), 123)
        self.assertEqual(
            cast_value(((Union[int, str], "param"), "abc")), "abc"
        )
        with self.assertRaises(ValueError):
            cast_value(((Union[int, bool], "param"), "abc"))

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

    def test_enum_casting(self):
        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        self.assertEqual(cast_value(((Color, "param"), "red")), Color.RED)
        with self.assertRaises(ValueError):
            cast_value(((Color, "param"), "green"))

    def test_literal_casting(self):
        self.assertEqual(
            cast_value(((Literal["yes", "no"], "param"), "yes")), "yes"
        )
        with self.assertRaises(ValueError):
            cast_value(((Literal["yes", "no"], "param"), "maybe"))

    def test_optional_with_union(self):
        self.assertEqual(cast_value(((Optional[int], "param"), None)), None)
        self.assertEqual(cast_value(((Optional[int], "param"), 5)), 5)

    def test_uuid_casting(self):
        uid = "12345678-1234-5678-1234-567812345678"
        result = cast_value(((UUID, "param"), uid))
        self.assertIsInstance(result, UUID)
        self.assertEqual(str(result), uid)

    def test_vector2_casting(self):
        v = cast_value(((Vector2, "param"), (1, 2)))
        self.assertIsInstance(v, Vector2)
        self.assertEqual((v.x, v.y), (1, 2))

    def test_decimal_fraction_casting(self):
        self.assertEqual(
            cast_value(((Decimal, "param"), "3.14")), Decimal("3.14")
        )
        self.assertEqual(
            cast_value(((Fraction, "param"), "3/4")), Fraction(3, 4)
        )

    def test_datetime_casting(self):
        dt_str = "2025-11-15T14:30:00"
        d_str = "2025-11-15"
        t_str = "14:30:00"
        self.assertEqual(
            cast_value(((datetime, "param"), dt_str)),
            datetime.fromisoformat(dt_str),
        )
        self.assertEqual(
            cast_value(((date, "param"), d_str)), date.fromisoformat(d_str)
        )
        self.assertEqual(
            cast_value(((time, "param"), t_str)), time.fromisoformat(t_str)
        )
        self.assertEqual(
            cast_value(((timedelta, "param"), "60")), timedelta(seconds=60)
        )

    def test_collection_casting(self):
        self.assertEqual(
            cast_value(((list, "param"), "1,2,3")), ["1", "2", "3"]
        )
        self.assertEqual(cast_value(((set, "param"), "a,b,a")), {"a", "b"})
        self.assertEqual(cast_value(((tuple, "param"), "x,y")), ("x", "y"))
        self.assertEqual(
            cast_value(((dict, "param"), '{"key": "value"}')), {"key": "value"}
        )

    def test_union_with_optional(self):
        self.assertEqual(cast_value(((Union[int, None], "param"), None)), None)
        self.assertEqual(cast_value(((Union[int, None], "param"), "42")), 42)

    def test_datetime_invalid(self):
        with self.assertRaises(ValueError):
            cast_value(((datetime, "param"), "not-a-date"))

    def test_fraction_invalid(self):
        with self.assertRaises(ValueError):
            cast_value(((Fraction, "param"), "abc"))

    def test_dict_invalid_string(self):
        with self.assertRaises(ValueError):
            cast_value(((dict, "param"), "not-json"))

    def test_enum_instance_roundtrip(self):
        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        self.assertEqual(cast_value(((Color, "param"), Color.RED)), Color.RED)

    def test_empty_string_optional(self):
        self.assertIsNone(cast_value(((Optional[int], "param"), "")))

    def test_empty_string_casts_to_none_for_optional(self):
        self.assertIsNone(cast_value(((Optional[str], "param"), "")))
        self.assertIsNone(cast_value(((Optional[int], "param"), "")))
        self.assertIsNone(cast_value(((Union[int, None], "param"), "")))
        self.assertEqual(cast_value(((str, "param"), "")), "")

    def test_empty_string_in_collections(self):
        self.assertEqual(
            cast_value(((Optional[list[str]], "param"), ",1.0")), [None, "1.0"]
        )
        self.assertEqual(
            cast_value(((Optional[tuple[str]], "param"), "a,,b")),
            ("a", None, "b"),
        )
        self.assertEqual(
            cast_value(((list[str], "param"), "x,,y")), ["x", "", "y"]
        )


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
