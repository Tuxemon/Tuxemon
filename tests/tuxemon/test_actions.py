# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest import mock

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
from tuxemon.db import Direction, MissionModel, MissionStatus, db
from tuxemon.player import Player
from tuxemon.session import local_session


def mockPlayer(self) -> None:
    self.name = "Jeff"
    self.money = {}
    self.game_variables = {}
    self.tuxepedia = {}


class TestVariableActions(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player

    def test_set_variable(self):
        self.action.execute_action("set_variable", ["name:jimmy"])
        self.assertEqual(self.player.game_variables["name"], "jimmy")

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
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player

    def test_set_player_name(self):
        self.action.execute_action("set_player_name", ["jimmy"])
        self.assertEqual(self.player.name, "jimmy")

    def test_set_player_name_random(self):
        self.action.execute_action("set_player_name", ["maple123:maple321"])
        self.assertIn(self.player.name, ["maple123", "maple321"])


class TestTuxepediaActions(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player
            _model = {"rockitten": 1}
            db.database["monster"] = _model

    def test_set_tuxepedia_seen(self):
        _params = ["player", "rockitten", "seen"]
        self.action.execute_action("set_tuxepedia", _params)
        self.assertEqual(self.player.tuxepedia["rockitten"], "seen")

    def test_set_tuxepedia_caught(self):
        _params = ["player", "rockitten", "caught"]
        self.action.execute_action("set_tuxepedia", _params)
        self.assertEqual(self.player.tuxepedia["rockitten"], "caught")

    def test_set_tuxepedia_wrong_seen_status(self):
        _params = ["player", "rockitten", "jimmy"]
        with self.assertRaises(ValueError):
            self.action.execute_action("set_tuxepedia", _params)

    def test_set_tuxepedia_wrong_monster(self):
        _params = ["player", "jimmy", "seen"]
        with self.assertRaises(ValueError):
            self.action.execute_action("set_tuxepedia", _params)

    def test_clear_tuxepedia_not_exist(self):
        with self.assertRaises(KeyError):
            self.action.execute_action("clear_tuxepedia", ["rockitten"])

    def test_clear_tuxepedia_exist(self):
        _params = ["player", "rockitten", "caught"]
        self.action.execute_action("set_tuxepedia", _params)
        self.action.execute_action("clear_tuxepedia", ["rockitten"])
        self.assertIsNone(self.player.tuxepedia.get("rockitten"))


class TestBattleActions(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
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


class TestMissionActions(unittest.TestCase):
    _mission = MissionModel(slug="no_type")
    _pending = MissionStatus.pending
    _failed = MissionStatus.failed
    _completed = MissionStatus.completed

    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player
            self.player.missions = []
            self._mission_model = {"no_type": self._mission}
            db.database["mission"] = self._mission_model

    def test_set_mission_add_success(self):
        _params = ["player", "no_type", "add"]
        self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 1)
        self.assertEqual(self.player.missions[0].slug, "no_type")
        self.assertEqual(self.player.missions[0].status, self._pending)

    def test_set_mission_add_fail(self):
        _params = ["player", "no_type", "jimmy"]
        with self.assertRaises(ValueError):
            self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 0)

    def test_set_mission_add_multiple(self):
        self._mission_model["town"] = MissionModel(slug="town")
        self._mission_model["route"] = MissionModel(slug="route")
        for slug in self._mission_model.keys():
            _params = ["player", slug, "add"]
            self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 3)

    def test_set_mission_add_status_success(self):
        _params = ["player", "no_type", "add", "completed"]
        self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 1)
        self.assertEqual(self.player.missions[0].status, self._completed)

    def test_set_mission_add_status_fail(self):
        _params = ["player", "no_type", "add", "jimmy"]
        with self.assertRaises(ValueError):
            self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 0)

    def test_set_mission_change_success(self):
        _params = ["player", "no_type", "add"]
        self.action.execute_action("set_mission", _params)
        _params = ["player", "no_type", "change", "failed"]
        self.action.execute_action("set_mission", _params)
        self.assertEqual(self.player.missions[0].status, self._failed)

    def test_set_mission_change_fail(self):
        _params = ["player", "no_type", "add"]
        self.action.execute_action("set_mission", _params)
        _params = ["player", "no_type", "change", "jimmy"]
        with self.assertRaises(ValueError):
            self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 1)

    def test_set_mission_remove_success(self):
        _params = ["player", "no_type", "add"]
        self.action.execute_action("set_mission", _params)
        _params = ["player", "no_type", "remove"]
        self.action.execute_action("set_mission", _params)
        self.assertEqual(len(self.player.missions), 0)


class TestCharacterActions(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player

    def test_char_speed_between_limits(self):
        self.player.moverate = prepare.CONFIG.player_walkrate
        self.action.execute_action("char_speed", ["player", 6.9])
        self.assertEqual(self.player.moverate, 6.9)

    def test_char_speed_outside_limits(self):
        self.player.moverate = prepare.CONFIG.player_walkrate
        lower, upper = prepare.MOVERATE_RANGE
        with self.assertRaises(ValueError):
            self.action.execute_action("char_speed", ["player", lower - 1])
        with self.assertRaises(ValueError):
            self.action.execute_action("char_speed", ["player", upper + 1])

    def test_char_walk(self):
        self.player.moverate = 6.9
        self.action.execute_action("char_walk", ["player"])
        self.assertEqual(self.player.moverate, prepare.CONFIG.player_walkrate)

    def test_char_run(self):
        self.player.moverate = 6.9
        self.action.execute_action("char_run", ["player"])
        self.assertEqual(self.player.moverate, prepare.CONFIG.player_runrate)

    def test_char_face(self):
        self.player.isplayer = False
        self.player.facing = Direction.down
        self.action.execute_action("char_face", ["player", "up"])
        self.assertEqual(self.player.facing, Direction.up)
