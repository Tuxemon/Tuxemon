# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest import mock

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
from tuxemon.player import Player
from tuxemon.session import local_session


def mockPlayer(self) -> None:
    self.money = {}
    self.game_variables = {}


class TestMoneyActions(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player

    def test_set_money_positive(self):
        self.action.execute_action("set_money", ["player", 200])
        self.assertEqual(self.player.money["player"], 200)

    def test_set_money_negative(self):
        with self.assertRaises(AttributeError):
            self.action.execute_action("set_money", ["player", -200])

    def test_modify_money(self):
        self.action.execute_action("modify_money", ["player", 100])
        self.assertEqual(self.player.money["player"], 100)
        with self.assertRaises(AttributeError):
            self.action.execute_action("modify_money", ["player", -200])
        self.assertEqual(self.player.money["player"], 100)
        self.action.execute_action("modify_money", ["player", -50])
        self.assertEqual(self.player.money["player"], 50)

    def test_modify_money_variable_str(self):
        self.action.execute_action("set_variable", [f"name:{50}"])
        self.assertEqual(self.player.game_variables["name"], "50")
        with self.assertRaises(ValueError):
            _params = ["player", None, "name"]
            self.action.execute_action("modify_money", _params)

    def test_modify_money_variable_float(self):
        self.action.execute_action("modify_money", ["player", 100])
        self.action.execute_action("set_variable", [f"name:{float(0.5)}"])
        self.action.execute_action("format_variable", ["name", "float"])
        _params = ["player", None, "name"]
        self.action.execute_action("modify_money", _params)
        self.assertEqual(self.player.money["player"], 150)

    def test_modify_money_variable_int(self):
        self.action.execute_action("set_variable", [f"name:{int(50)}"])
        self.action.execute_action("format_variable", ["name", "int"])
        _params = ["player", None, "name"]
        self.action.execute_action("modify_money", _params)
        self.assertEqual(self.player.money["player"], int(50))

    def test_transfer_money_negative_value(self):
        self.action.execute_action("set_money", ["player", 100])
        _params = ["player", -50, "jim"]
        with self.assertRaises(AttributeError):
            self.action.execute_action("transfer_money", _params)

    def test_transfer_money_positive_value(self):
        self.action.execute_action("set_money", ["player", 100])
        _params = ["player", 500, "jim"]
        with self.assertRaises(AttributeError):
            self.action.execute_action("transfer_money", _params)
        self.action.execute_action("transfer_money", ["player", 50, "jim"])
        self.assertEqual(self.player.money["player"], 50)
        self.assertEqual(self.player.money["jim"], 50)
