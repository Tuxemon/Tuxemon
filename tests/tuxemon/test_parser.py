# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

yes, these results are wacky, but they are here for regression testing

"""

import unittest

from tuxemon.script.parser import (
    parse_action_string,
    parse_condition_string,
    split_escaped,
)


class TestSplitEscaped(unittest.TestCase):
    def test_one_word(self):
        result = split_escaped("spam")
        self.assertEqual(["spam"], result)

    def test_trailing_space(self):
        result = split_escaped("spam ")
        self.assertEqual(["spam"], result)

    def test_leading_space(self):
        result = split_escaped(" spam")
        self.assertEqual(["spam"], result)

    def test_enclosed_space(self):
        result = split_escaped(" spam ")
        self.assertEqual(["spam"], result)

    def test_space_around_arg(self):
        result = split_escaped("spam , eggs  ")
        self.assertEqual(["spam", "eggs"], result)

    def test_trailing_comma(self):
        result = split_escaped("spam , eggs,")
        self.assertEqual(["spam", "eggs", ""], result)

    def test_double_comma(self):
        result = split_escaped("spam , eggs  ,, ")
        self.assertEqual(["spam", "eggs", "", ""], result)

    def test_empty(self):
        result = split_escaped("")
        self.assertEqual([""], result)

    def test_only_comma(self):
        result = split_escaped(",")
        self.assertEqual(["", ""], result)


class TestParseActionString(unittest.TestCase):
    def test_action_no_arg(self):
        result = parse_action_string("spam")
        self.assertEqual(("spam", []), result)

    def test_action_and_arg(self):
        result = parse_action_string("spam eggs")
        self.assertEqual(("spam", ["eggs"]), result)

    def test_action_and_args(self):
        result = parse_action_string("spam eggs,parrot")
        self.assertEqual(("spam", ["eggs", "parrot"]), result)

    def test_action_and_comma(self):
        result = parse_action_string("spam , ")
        self.assertEqual(("spam", ["", ""]), result)

    def test_action_arg_and_trailing_comma(self):
        result = parse_action_string("spam eggs, ")
        self.assertEqual(("spam", ["eggs", ""]), result)

    def test_no_space_between_comma(self):
        result = parse_action_string("spam,eggs")
        self.assertEqual(("spam,eggs", []), result)

    def test_enclosed_space(self):
        result = parse_action_string("   spam   ")
        self.assertEqual(("", ["spam"]), result)

    def test_double_comma(self):
        result = parse_action_string("spam ,,")
        self.assertEqual(("spam", ["", "", ""]), result)

    def test_space_in_arg1(self):
        result = parse_action_string("spam ex parrot")
        self.assertEqual(("spam", ["ex parrot"]), result)

    def test_space_in_arg2(self):
        result = parse_action_string("spam eggs,  ex parrot")
        self.assertEqual(("spam", ["eggs", "ex parrot"]), result)


class TestParseConditionString(unittest.TestCase):
    def test_no_type(self):
        with self.assertRaises(ValueError):
            parse_condition_string("spam")

    def test_no_args(self):
        result = parse_condition_string("spam eggs")
        self.assertEqual(("spam", "eggs", []), result)

    def test_enclosed_space(self):
        result = parse_condition_string(" spam eggs ")
        self.assertEqual(("", "spam", ["eggs"]), result)

    def test_trailing_comma(self):
        result = parse_condition_string("spam eggs, ")
        self.assertEqual(("spam", "eggs,", [""]), result)

    def test_with_args(self):
        result = parse_condition_string("spam eggs, parrot")
        self.assertEqual(("spam", "eggs,", ["parrot"]), result)

    def test_with_args_trailing_comma(self):
        result = parse_condition_string(" spam eggs parrot, cheese, ")
        self.assertEqual(("", "spam", ["eggs parrot", "cheese", ""]), result)

    def test_space_in_arg(self):
        result = parse_condition_string("spam eggs  ex parrot, cheese shop")
        self.assertEqual(
            ("spam", "eggs", ["ex parrot", "cheese shop"]),
            result,
        )
