# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import math
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Literal
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from tuxemon.entity.player import Player
from tuxemon.math import Vector2
from tuxemon.tools import (
    cast_value,
    check_condition,
    compare,
    copy_dict_with_keys,
    number_or_variable,
    parse_flag,
    round_to_divisible,
)


@pytest.mark.parametrize(
    "value, divisor, expected",
    [
        pytest.param(1, 16, 0, id="round_down"),
        pytest.param(15, 16, 16, id="round_up"),
        pytest.param(24, 16, 32, id="round_up_half"),
        pytest.param(51, 100, 100, id="alternate_divisor"),
    ],
)
def test_round_to_divisible_basic(value, divisor, expected):
    assert round_to_divisible(value, divisor) == expected


def test_return_type_is_int():
    assert type(round_to_divisible(0)) is int


# copy_dict_with_keys


@pytest.mark.parametrize(
    "source, keys, expected",
    [
        pytest.param(
            {"a": 1, "b": 2, "c": 3},
            ["a", "c"],
            {"a": 1, "c": 3},
            id="basic_subset",
        ),
    ],
)
def test_copy_dict_with_keys(source, keys, expected):
    assert copy_dict_with_keys(source, keys) == expected


# number_or_variable


@pytest.fixture
def player():
    p = MagicMock(spec=Player)
    p.game_variables = {
        "my_var": 2,
        "non_numeric": "text",
        "none_value": None,
    }
    return p


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("1", 1.0, id="int_string"),
        pytest.param("1.5", 1.5, id="float_string"),
    ],
)
def test_numeric_string(player, value, expected):
    assert number_or_variable(player.game_variables, value) == expected


def test_variable_name(player):
    assert number_or_variable(player.game_variables, "my_var") == 2.0


def test_unbound_variable(player):
    with pytest.raises(ValueError):
        number_or_variable(player.game_variables, "unbound_var")


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("1.5.3", id="multiple_dots"),
        pytest.param("-1..5", id="double_dot_negative"),
    ],
)
def test_invalid_numeric_string(player, value):
    with pytest.raises(ValueError):
        number_or_variable(player.game_variables, value)


def test_empty_string(player):
    with pytest.raises(ValueError):
        number_or_variable(player.game_variables, "")


def test_negative_number(player):
    assert number_or_variable(player.game_variables, "-10") == -10.0


def test_zero(player):
    assert number_or_variable(player.game_variables, "0") == 0.0


def test_scientific_notation(player):
    assert number_or_variable(player.game_variables, "1e3") == 1000.0


def test_non_numeric_variable(player):
    with pytest.raises(ValueError):
        number_or_variable(player.game_variables, "non_numeric")


def test_none_variable(player):
    with pytest.raises(ValueError):
        number_or_variable(player.game_variables, "none_value")


# cast_value


@pytest.mark.parametrize(
    "typeinfo, value, expected",
    [
        pytest.param((int, "param"), 42, 42, id="int_from_int"),
        pytest.param((int, "param"), "42", 42, id="int_from_str"),
        pytest.param((int, "param"), "3.0", 3, id="int_from_float_str"),
        pytest.param((float, "param"), 3.14, 3.14, id="float_from_float"),
        pytest.param((float, "param"), "42", 42.0, id="float_from_str"),
        pytest.param((str, "param"), "hello", "hello", id="str_from_str"),
        pytest.param((str, "param"), 123, "123", id="str_from_int"),
        pytest.param((bool, "param"), True, True, id="bool_true"),
        pytest.param((bool, "param"), False, False, id="bool_false"),
        pytest.param((bool, "param"), "true", True, id="bool_from_true_str"),
        pytest.param(
            (bool, "param"), "false", False, id="bool_from_false_str"
        ),
        pytest.param((bool, "param"), "yes", True, id="bool_from_yes"),
        pytest.param((bool, "param"), "no", False, id="bool_from_no"),
        pytest.param((bool, "param"), "1", True, id="bool_from_1"),
        pytest.param((bool, "param"), "0", False, id="bool_from_0"),
    ],
)
def test_basic_types(typeinfo, value, expected):
    assert cast_value((typeinfo, value)) == expected


def test_none_handling():
    with pytest.raises(ValueError):
        cast_value(((str, "param"), None))


def test_literal_types():
    with pytest.raises(ValueError):
        cast_value(((Literal[1, 2, 3], "param"), 4))


@pytest.mark.parametrize(
    "typeinfo, value, expected",
    [
        pytest.param((int | str, "param"), 123, 123, id="union_int"),
        pytest.param((int | str, "param"), "abc", "abc", id="union_str"),
    ],
)
def test_union_types_valid(typeinfo, value, expected):
    assert cast_value((typeinfo, value)) == expected


def test_union_types_invalid():
    with pytest.raises(ValueError):
        cast_value(((int | bool, "param"), "abc"))


def test_sequence_of_types_combinations():
    with pytest.raises(ValueError):
        cast_value(((int, str, bool), True))


@pytest.mark.parametrize(
    "typeinfo, value, expected",
    [
        pytest.param((int | None, "param"), None, None, id="optional_none"),
        pytest.param((int | None, "param"), 5, 5, id="optional_int"),
    ],
)
def test_optional_with_union(typeinfo, value, expected):
    assert cast_value((typeinfo, value)) == expected


def test_optional_types_and_sequences():
    assert cast_value(((int | None, str), None)) is None
    with pytest.raises(ValueError):
        cast_value(((int | None, None, str), True))


def test_edge_cases_with_sequences():
    with pytest.raises(ValueError):
        cast_value((([], "param"), 42))
    with pytest.raises(ValueError):
        cast_value(((None, None, "param"), None))


def test_enum_casting():
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    assert cast_value(((Color, "param"), "red")) == Color.RED

    with pytest.raises(ValueError):
        cast_value(((Color, "param"), "green"))


def test_literal_casting():
    assert cast_value(((Literal["yes", "no"], "param"), "yes")) == "yes"

    with pytest.raises(ValueError):
        cast_value(((Literal["yes", "no"], "param"), "maybe"))


def test_uuid_casting():
    uid = "12345678-1234-5678-1234-567812345678"
    result = cast_value(((UUID, "param"), uid))
    assert isinstance(result, UUID)
    assert str(result) == uid


def test_vector2_casting():
    v = cast_value(((Vector2, "param"), (1, 2)))
    assert isinstance(v, Vector2)
    assert (v.x, v.y) == (1, 2)


@pytest.mark.parametrize(
    "typeinfo, value, expected",
    [
        pytest.param(
            (Decimal, "param"), "3.14", Decimal("3.14"), id="decimal"
        ),
        pytest.param(
            (Fraction, "param"), "3/4", Fraction(3, 4), id="fraction"
        ),
    ],
)
def test_decimal_fraction_casting(typeinfo, value, expected):
    assert cast_value((typeinfo, value)) == expected


def test_datetime_casting():
    dt_str = "2025-11-15T14:30:00"
    d_str = "2025-11-15"
    t_str = "14:30:00"

    assert cast_value(((datetime, "param"), dt_str)) == datetime.fromisoformat(
        dt_str
    )
    assert cast_value(((date, "param"), d_str)) == date.fromisoformat(d_str)
    assert cast_value(((time, "param"), t_str)) == time.fromisoformat(t_str)
    assert cast_value(((timedelta, "param"), "60")) == timedelta(seconds=60)


@pytest.mark.parametrize(
    "typeinfo, value, expected",
    [
        pytest.param((list, "param"), "1,2,3", ["1", "2", "3"], id="list"),
        pytest.param((set, "param"), "a,b,a", {"a", "b"}, id="set"),
        pytest.param((tuple, "param"), "x,y", ("x", "y"), id="tuple"),
        pytest.param(
            (dict, "param"), '{"key": "value"}', {"key": "value"}, id="dict"
        ),
    ],
)
def test_collection_casting(typeinfo, value, expected):
    assert cast_value((typeinfo, value)) == expected


def test_datetime_invalid():
    with pytest.raises(ValueError):
        cast_value(((datetime, "param"), "not-a-date"))


def test_fraction_invalid():
    with pytest.raises(ValueError):
        cast_value(((Fraction, "param"), "abc"))


def test_dict_invalid_string():
    with pytest.raises(ValueError):
        cast_value(((dict, "param"), "not-json"))


def test_enum_instance_roundtrip():
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    assert cast_value(((Color, "param"), Color.RED)) == Color.RED


def test_empty_string_optional():
    assert cast_value(((int | None, "param"), "")) is None


def test_empty_string_casts_to_none_for_optional():
    assert cast_value(((str | None, "param"), "")) is None
    assert cast_value(((int | None, "param"), "")) is None
    assert cast_value(((int | None, "param"), "")) is None
    assert cast_value(((str, "param"), "")) == ""


def test_empty_string_in_collections():
    assert cast_value(((list[str] | None, "param"), ",1.0")) == [None, "1.0"]
    assert cast_value(((tuple[str] | None, "param"), "a,,b")) == (
        "a",
        None,
        "b",
    )
    assert cast_value(((list[str], "param"), "x,,y")) == ["x", "", "y"]


# compare


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("<", 2, 3, True, id="lt_true"),
        pytest.param("<", 3, 2, False, id="lt_false"),
    ],
)
def test_less_than(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("<=", 2, 3, True, id="le_true_lt"),
        pytest.param("<=", 2, 2, True, id="le_true_eq"),
        pytest.param("<=", 3, 2, False, id="le_false"),
    ],
)
def test_less_or_equal(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param(">", 3, 2, True, id="gt_true"),
        pytest.param(">", 2, 3, False, id="gt_false"),
    ],
)
def test_greater_than(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param(">=", 3, 2, True, id="ge_true_gt"),
        pytest.param(">=", 2, 2, True, id="ge_true_eq"),
        pytest.param(">=", 2, 3, False, id="ge_false"),
    ],
)
def test_greater_or_equal(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("==", 2, 2, True, id="eq_true"),
        pytest.param("==", 3, 2, False, id="eq_false"),
    ],
)
def test_equals(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("!=", 2, 3, True, id="ne_true"),
        pytest.param("!=", 2, 2, False, id="ne_false"),
    ],
)
def test_not_equals(op, a, b, expected):
    assert compare(op, a, b) is expected


def test_invalid_operator():
    with pytest.raises(ValueError):
        compare("invalid", 2, 3)


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("<", 2.5, 3.0, True, id="float_lt"),
        pytest.param(">=", 3.0, 2.5, True, id="float_ge"),
    ],
)
def test_float_values(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("==", 0, 0, True, id="zero_eq"),
        pytest.param("!=", 0, 0, False, id="zero_ne"),
        pytest.param(">=", 0, -1, True, id="zero_ge"),
        pytest.param("<=", 0, 1, True, id="zero_le"),
    ],
)
def test_zero_values(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param(">", math.inf, 5, True, id="inf_gt"),
        pytest.param("<", -math.inf, 5, True, id="neg_inf_lt"),
    ],
)
def test_infinity(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("==", math.nan, math.nan, False, id="nan_eq_false"),
        pytest.param("!=", math.nan, math.nan, True, id="nan_ne_true"),
    ],
)
def test_nan(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        pytest.param("==", 2, 2.0, True, id="int_float_eq"),
        pytest.param("<", 2.5, 3, True, id="float_int_lt"),
    ],
)
def test_int_and_float(op, a, b, expected):
    assert compare(op, a, b) is expected


@pytest.mark.parametrize(
    "op, a, b",
    [
        pytest.param("<", "a", 5, id="invalid_left"),
        pytest.param(">", 3, "b", id="invalid_right"),
    ],
)
def test_invalid_data_types(op, a, b):
    with pytest.raises(TypeError):
        compare(op, a, b)


# parse_flag


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("true", True, id="true_lower"),
        pytest.param("True", True, id="true_capitalized"),
        pytest.param("1", True, id="one"),
        pytest.param("yes", True, id="yes_lower"),
        pytest.param("YeS", True, id="yes_mixed_case"),
    ],
)
def test_parse_flag_truthy(value, expected):
    assert parse_flag(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("false", False, id="false_lower"),
        pytest.param("0", False, id="zero"),
        pytest.param("no", False, id="no_lower"),
        pytest.param("", False, id="empty_string"),
        pytest.param(None, False, id="none_value"),
        pytest.param("maybe", False, id="invalid_word"),
    ],
)
def test_parse_flag_falsy(value, expected):
    assert parse_flag(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("  yes  ", True, id="trimmed_yes"),
        pytest.param("  no  ", False, id="trimmed_no"),
        pytest.param("YES!", False, id="punctuated_yes"),
        pytest.param("truEly", False, id="substring_true"),
        pytest.param("2", False, id="numeric_two"),
        pytest.param("-1", False, id="negative_one"),
    ],
)
def test_parse_flag_edge_cases(value, expected):
    assert parse_flag(value) is expected


# check_condition


@pytest.mark.parametrize(
    "text, dataset, expected",
    [
        pytest.param(
            "fire", {"fire", "water", "earth"}, True, id="positive_match"
        ),
        pytest.param(
            "Water", {"fire", "water", "earth"}, True, id="case_insensitive"
        ),
        pytest.param(
            "air", {"fire", "water", "earth"}, False, id="missing_value"
        ),
    ],
)
def test_check_condition_positive(text, dataset, expected):
    assert check_condition(text, dataset) is expected


@pytest.mark.parametrize(
    "text, dataset, expected",
    [
        pytest.param(
            "!air", {"fire", "water", "earth"}, True, id="negation_missing"
        ),
        pytest.param(
            "!fire", {"fire", "water", "earth"}, False, id="negation_present"
        ),
    ],
)
def test_check_condition_negative(text, dataset, expected):
    assert check_condition(text, dataset) is expected


@pytest.mark.parametrize(
    "text, dataset, expected",
    [
        pytest.param("", {"fire"}, False, id="empty_string"),
        pytest.param("   ", {"fire"}, False, id="whitespace_only"),
    ],
)
def test_check_condition_empty(text, dataset, expected):
    assert check_condition(text, dataset) is expected


@pytest.mark.parametrize(
    "text, dataset, expected",
    [
        pytest.param(
            "  fire  ", {"fire", "water"}, True, id="trimmed_positive"
        ),
        pytest.param(
            "!  earth  ", {"fire", "water"}, True, id="trimmed_negation"
        ),
        pytest.param("!!fire", {"fire", "water"}, True, id="double_negation"),
        pytest.param("fire", set(), False, id="empty_set_positive"),
        pytest.param("!fire", set(), True, id="empty_set_negation"),
        pytest.param("!", {"fire", "water"}, True, id="bare_negation"),
        pytest.param("   ", {"fire", "water"}, False, id="whitespace_again"),
    ],
)
def test_check_condition_edge_cases(text, dataset, expected):
    assert check_condition(text, dataset) is expected
