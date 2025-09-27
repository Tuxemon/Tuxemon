# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon import prepare
from tuxemon.db import Direction
from tuxemon.entity import Body, Mover
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.running import ConditionEvaluator
from tuxemon.game_variables import GameVariablesManager
from tuxemon.math import Point3, Vector3
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.tuxepedia import Tuxepedia


def mockPlayer(self) -> None:
    self.name = "Jeff"
    self._variables = GameVariablesManager()
    self.tuxepedia = Tuxepedia()
    self.body = Body(Point3(0, 0, 0))
    self.mover = Mover(self.body)


class TestVariableActions(unittest.TestCase):
    def setUp(self):
        action = ActionManager()
        evaluator = ConditionEvaluator(MagicMock(), MagicMock())
        self.mock_screen = MagicMock()
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session, action, evaluator)
            local_session.set_player(Player())
            self.player = local_session.player

    def test_set_variable(self):
        self.action.execute_action("set_variable", ["name:jimmy"])
        self.assertEqual(self.player.game_variables.get("name"), "jimmy")

    def test_set_variables_same_key(self):
        self.action.execute_action("set_variable", ["name:jimmy", "name:saul"])
        self.assertEqual(self.player.game_variables.get("name"), "saul")

    def test_set_variables_different_key(self):
        self.action.execute_action(
            "set_variable", ["first:jimmy", "last:saul"]
        )
        self.assertEqual(self.player.game_variables.get("first"), "jimmy")
        self.assertEqual(self.player.game_variables.get("last"), "saul")

    def test_clear_variable_not_exist(self):
        self.action.execute_action("clear_variable", ["name"])
        self.assertIsNone(self.player.game_variables.get("name"))

    def test_clear_variable_exist(self):
        self.action.execute_action("set_variable", ["name:jimmy"])
        self.action.execute_action("clear_variable", ["name"])
        self.assertIsNone(self.player.game_variables.get("name"))

    def test_clear_multiple_variables_exist(self):
        self.action.execute_action(
            "set_variable", ["first:jimmy", "last:saul"]
        )
        self.action.execute_action("clear_variable", ["first", "last"])
        self.assertIsNone(self.player.game_variables.get("first"))
        self.assertIsNone(self.player.game_variables.get("last"))

    def test_clear_multiple_variables_exist_and_not(self):
        self.action.execute_action("set_variable", ["last:saul"])
        self.action.execute_action("clear_variable", ["first", "last"])
        self.assertIsNone(self.player.game_variables.get("first"))
        self.assertIsNone(self.player.game_variables.get("last"))

    def test_copy_variable(self):
        self.action.execute_action("set_variable", ["name:jeff"])
        self.action.execute_action("copy_variable", ["friend", "name"])
        self.assertEqual(self.player.game_variables.get("friend"), "jeff")

    def test_format_variable_float(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "float"])
        self.assertEqual(self.player.game_variables.get("age"), 69.0)

    def test_format_variable_int(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "int"])
        self.assertEqual(self.player.game_variables.get("age"), 69)

    def test_format_variable_negative_float(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "-float"])
        self.assertEqual(self.player.game_variables.get("age"), -69.0)

    def test_format_variable_negative_int(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "-int"])
        self.assertEqual(self.player.game_variables.get("age"), -69)

    def test_format_variable_wrong_format(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        with self.assertRaises(ValueError):
            self.action.execute_action("format_variable", ["age", "jimmy"])

    def test_random_integer(self):
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        self.action.execute_action("format_variable", ["lucky", "int"])
        self.assertGreaterEqual(self.player.game_variables.get("lucky"), 1)
        self.assertLessEqual(self.player.game_variables.get("lucky"), 5)

    def test_set_random_variable(self):
        _params = ["choice", "rockitten:agnite"]
        self.action.execute_action("set_random_variable", _params)
        _container = ["rockitten", "agnite"]
        self.assertIn(self.player.game_variables.get("choice"), _container)

    def test_variable_math_sum(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["age", "+", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        self.assertGreaterEqual(self.player.game_variables.get("result"), 70)
        self.assertLessEqual(self.player.game_variables.get("result"), 74)

    def test_variable_math_subtraction(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["lucky", "-", "age", "result"]
        with self.assertRaises(AssertionError):
            self.action.execute_action("variable_math", _params)
            self.assertGreaterEqual(
                self.player.game_variables.get("result"), 70
            )
            self.assertLessEqual(self.player.game_variables.get("result"), 74)
        self.assertGreaterEqual(self.player.game_variables.get("result"), -68)
        self.assertLessEqual(self.player.game_variables.get("result"), -64)
        _params = ["age", "-", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        self.assertGreaterEqual(self.player.game_variables.get("result"), 64)
        self.assertLessEqual(self.player.game_variables.get("result"), 68)

    def test_variable_math_division(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["age", "/", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        _container_int = [69, 34, 23, 17, 13]
        self.assertIn(self.player.game_variables.get("result"), _container_int)

    def test_variable_math_multiplication(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["age", "*", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        _container = [69, 138, 207, 276, 345]
        self.assertIn(self.player.game_variables.get("result"), _container)


class TestActionsSetPlayer(unittest.TestCase):
    def setUp(self):
        action = ActionManager()
        evaluator = ConditionEvaluator(MagicMock(), MagicMock())
        self.mock_screen = MagicMock()
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session, action, evaluator)
            local_session.set_player(Player())
            self.player = local_session.player

    def test_set_player_name(self):
        self.action.execute_action("set_player_name", ["jimmy"])
        self.assertEqual(self.player.name, "jimmy")

    def test_set_player_name_random(self):
        self.action.execute_action("set_player_name", ["maple123:maple321"])
        self.assertIn(self.player.name, ["maple123", "maple321"])


class TestCharacterActions(unittest.TestCase):
    def setUp(self):
        action = ActionManager()
        evaluator = ConditionEvaluator(MagicMock(), MagicMock())
        self.mock_screen = MagicMock()
        local_session.set_client(MagicMock())
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session, action, evaluator)
            local_session.set_player(Player())
            self.player = local_session.player

    def test_char_speed_between_limits(self):
        self.player.mover.walking()
        self.action.execute_action("char_speed", ["player", 6.9])
        self.assertEqual(self.player.moverate, 6.9)

    def test_char_speed_outside_limits(self):
        self.player.mover.walking()
        lower, upper = prepare.MOVERATE_RANGE
        with self.assertRaises(ValueError):
            self.action.execute_action("char_speed", ["player", lower - 1])
        with self.assertRaises(ValueError):
            self.action.execute_action("char_speed", ["player", upper + 1])

    def test_char_walk(self):
        self.player.set_moverate(6.9)
        self.player.body.velocity = Vector3(1, 0, 0)
        self.action.execute_action("char_walk", ["player"])
        self.assertEqual(self.player.moverate, prepare.CONFIG.player_walkrate)

    def test_char_run(self):
        self.player.set_moverate(6.9)
        self.player.body.velocity = Vector3(1, 0, 0)
        self.action.execute_action("char_run", ["player"])
        self.assertEqual(self.player.moverate, prepare.CONFIG.player_runrate)
