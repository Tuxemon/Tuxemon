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


class TestMoney(unittest.TestCase):
    def test_var(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            # session = Session()
            player = Player()
            local_session.player = player
            config = prepare.CONFIG
            _client = LocalPygameClient(config)
            local_session.client = _client
            action = local_session.client.event_engine

            # set_money
            action.execute_action("set_money", ["player", 200])
            self.assertEqual(player.money["player"], 200)

            with self.assertRaises(AttributeError):
                action.execute_action("set_money", ["player", -200])
            self.assertEqual(player.money["player"], 200)

            action.execute_action("set_money", ["player", 0])
            self.assertEqual(player.money["player"], 0)

            # modify_money
            action.execute_action("modify_money", ["player", 0])
            self.assertEqual(player.money["player"], 0)

            action.execute_action("modify_money", ["player", 100])
            self.assertEqual(player.money["player"], 100)

            with self.assertRaises(AttributeError):
                action.execute_action("modify_money", ["player", -200])
            self.assertEqual(player.money["player"], 100)

            action.execute_action("modify_money", ["player", -50])
            self.assertEqual(player.money["player"], 50)

            # transfer_money
            with self.assertRaises(AttributeError):
                action.execute_action("transfer_money", ["player", -50, "jim"])
            self.assertEqual(player.money["player"], 50)

            with self.assertRaises(AttributeError):
                action.execute_action("transfer_money", ["player", 500, "jim"])
            self.assertEqual(player.money["player"], 50)

            action.execute_action("transfer_money", ["player", 50, "jim"])
            self.assertEqual(player.money["player"], 0)
            self.assertEqual(player.money["jim"], 50)
