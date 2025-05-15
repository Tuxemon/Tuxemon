# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon import prepare
from tuxemon.db import Direction
from tuxemon.entity import Body, Mover
from tuxemon.event.eventengine import EventEngine
from tuxemon.math import Point3, Vector3
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.tuxepedia import Tuxepedia


def mockPlayer(self) -> None:
    self.name = "Jeff"
    self.game_variables = {}
    self.tuxepedia = Tuxepedia()
    self.body = Body(Point3(0, 0, 0))
    self.mover = Mover(self.body)


class TestVariableActions(unittest.TestCase):
    def setUp(self):
        self.mock_screen = MagicMock()
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session)
            local_session.player = Player()
            self.player = local_session.player

    def test_set_variable(self):
        self.action.execute_action("set_variable", ["name:jimmy"])
        self.assertEqual(self.player.game_variables["name"], "jimmy")

    def test_set_variables_same_key(self):
        self.action.execute_action("set_variable", ["name:jimmy", "name:saul"])
        self.assertEqual(self.player.game_variables["name"], "saul")

    def test_set_variables_different_key(self):
        self.action.execute_action(
            "set_variable", ["first:jimmy", "last:saul"]
        )
        self.assertEqual(self.player.game_variables["first"], "jimmy")
        self.assertEqual(self.player.game_variables["last"], "saul")

    def test_clear_variable_not_exist(self):
        self.action.execute_action("clear_variable", ["name"])
        with self.assertRaises(KeyError):
            self.assertIsNotNone(self.player.game_variables["name"])

    def test_clear_variable_exist(self):
        self.action.execute_action("set_variable", ["name:jimmy"])
        self.action.execute_action("clear_variable", ["name"])
        self.assertIsNone(self.player.game_variables.get("name"))

    def test_copy_variable(self):
        self.action.execute_action("set_variable", ["name:jeff"])
        self.action.execute_action("copy_variable", ["friend", "name"])
        self.assertEqual(self.player.game_variables["friend"], "jeff")

    def test_format_variable_float(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "float"])
        self.assertEqual(self.player.game_variables["age"], 69.0)

    def test_format_variable_int(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "int"])
        self.assertEqual(self.player.game_variables["age"], 69)

    def test_format_variable_negative_float(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "-float"])
        self.assertEqual(self.player.game_variables["age"], -69.0)

    def test_format_variable_negative_int(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("format_variable", ["age", "-int"])
        self.assertEqual(self.player.game_variables["age"], -69)

    def test_format_variable_wrong_format(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        with self.assertRaises(ValueError):
            self.action.execute_action("format_variable", ["age", "jimmy"])

    def test_random_integer(self):
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        self.action.execute_action("format_variable", ["lucky", "int"])
        self.assertGreaterEqual(self.player.game_variables["lucky"], 1)
        self.assertLessEqual(self.player.game_variables["lucky"], 5)

    def test_set_random_variable(self):
        _params = ["choice", "rockitten:agnite"]
        self.action.execute_action("set_random_variable", _params)
        _container = ["rockitten", "agnite"]
        self.assertIn(self.player.game_variables["choice"], _container)

    def test_variable_math_sum(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["age", "+", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        self.assertGreaterEqual(self.player.game_variables["result"], 70)
        self.assertLessEqual(self.player.game_variables["result"], 74)

    def test_variable_math_subtraction(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["lucky", "-", "age", "result"]
        with self.assertRaises(AssertionError):
            self.action.execute_action("variable_math", _params)
            self.assertGreaterEqual(self.player.game_variables["result"], 70)
            self.assertLessEqual(self.player.game_variables["result"], 74)
        self.assertGreaterEqual(self.player.game_variables["result"], -68)
        self.assertLessEqual(self.player.game_variables["result"], -64)
        _params = ["age", "-", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        self.assertGreaterEqual(self.player.game_variables["result"], 64)
        self.assertLessEqual(self.player.game_variables["result"], 68)

    def test_variable_math_division(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["age", "/", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        _container_int = [69, 34, 23, 17, 13]
        self.assertIn(self.player.game_variables["result"], _container_int)

    def test_variable_math_multiplication(self):
        self.action.execute_action("set_variable", [f"age:{69}"])
        self.action.execute_action("random_integer", ["lucky", 1, 5])
        _params = ["age", "*", "lucky", "result"]
        self.action.execute_action("variable_math", _params)
        _container = [69, 138, 207, 276, 345]
        self.assertIn(self.player.game_variables["result"], _container)


class TestActionsSetPlayer(unittest.TestCase):
    def setUp(self):
        self.mock_screen = MagicMock()
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session)
            local_session.player = Player()
            self.player = local_session.player

    def test_set_player_name(self):
        self.action.execute_action("set_player_name", ["jimmy"])
        self.assertEqual(self.player.name, "jimmy")

    def test_set_player_name_random(self):
        self.action.execute_action("set_player_name", ["maple123:maple321"])
        self.assertIn(self.player.name, ["maple123", "maple321"])


class TestBattleActions(unittest.TestCase):
    def setUp(self):
        self.mock_screen = MagicMock()
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session)
            local_session.player = Player()
            self.player = local_session.player

    def test_set_battle_won(self):
        self.player.battles = []
        self.player.steps = 0.0
        _params = ["figher", "won", "opponent"]
        self.action.execute_action("set_battle", _params)
        self.assertEqual(len(self.player.battles), 1)
        self.assertEqual(self.player.battles[0].fighter, "figher")
        self.assertEqual(self.player.battles[0].outcome, "won")
        self.assertEqual(self.player.battles[0].opponent, "opponent")
        self.assertEqual(self.player.battles[0].steps, 0)

    def test_set_battle_lost(self):
        self.player.battles = []
        self.player.steps = 0.0
        _params = ["figher", "lost", "opponent"]
        self.action.execute_action("set_battle", _params)
        self.assertEqual(len(self.player.battles), 1)
        self.assertEqual(self.player.battles[0].fighter, "figher")
        self.assertEqual(self.player.battles[0].outcome, "lost")
        self.assertEqual(self.player.battles[0].opponent, "opponent")
        self.assertEqual(self.player.battles[0].steps, 0)

    def test_set_battle_draw(self):
        self.player.battles = []
        self.player.steps = 0.0
        _params = ["figher", "draw", "opponent"]
        self.action.execute_action("set_battle", _params)
        self.assertEqual(len(self.player.battles), 1)
        self.assertEqual(self.player.battles[0].fighter, "figher")
        self.assertEqual(self.player.battles[0].outcome, "draw")
        self.assertEqual(self.player.battles[0].opponent, "opponent")
        self.assertEqual(self.player.battles[0].steps, 0)

    def test_set_battle_wrong(self):
        _params = ["figher", "jimmy", "opponent"]
        with self.assertRaises(ValueError):
            self.action.execute_action("set_battle", _params)


class TestCharacterActions(unittest.TestCase):
    def setUp(self):
        self.mock_screen = MagicMock()
        local_session.client = MagicMock()
        with patch.object(Player, "__init__", mockPlayer):
            self.action = EventEngine(local_session)
            local_session.player = Player()
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

    def test_char_face(self):
        self.player.isplayer = False
        self.player.set_facing(Direction.down)
        self.action.execute_action("char_face", ["player", "up"])
        self.assertEqual(self.player.facing, Direction.up)
