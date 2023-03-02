# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.tools import copy_dict_with_keys, round_to_divisible, number_or_variable
from tuxemon.session import local_session
from tuxemon.session import Session
from unittest import mock

from tuxemon.player import Player

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

class TestVariableMoney(unittest.TestCase):
    def test_var(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            #session = Session()
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