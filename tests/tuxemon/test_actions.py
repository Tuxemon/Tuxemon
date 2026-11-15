# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.entity.entity import Body, Mover
from tuxemon.entity.npc import NPC
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventbehavior import BehaviorManager
from tuxemon.event.eventbus import EventBus
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.running import ConditionEvaluator
from tuxemon.game_variables import GameVariablesManager
from tuxemon.math import Vector2
from tuxemon.platform.const.sizes import MOVERATE_RANGE
from tuxemon.session import local_session
from tuxemon.tuxepedia.manager import TuxepediaManager
from tuxemon.user_config import CONFIG


def mockPlayer(self):
    self.name = "Jeff"
    self._variables = GameVariablesManager()
    self.tuxepedia = TuxepediaManager(EventBus())
    self.body = Body(Vector2(0, 0))
    self.mover = Mover(self.body)


@pytest.fixture
def patched_player_init():
    with patch.object(NPC, "__init__", mockPlayer):
        yield


@pytest.fixture
def engine(patched_player_init):
    action = ActionManager()
    evaluator = ConditionEvaluator(MagicMock(), MagicMock())
    behavior = BehaviorManager()
    eng = EventEngine(local_session, action, evaluator, behavior)
    player = NPC()
    local_session.set_player(player)
    mock_client = MagicMock()
    mock_client.get_npc.side_effect = lambda slug: (
        player if slug == "player" else None
    )
    mock_client.get_npc_pos.return_value = None
    local_session.set_client(mock_client)
    return eng


@pytest.fixture
def player():
    return local_session.player


def test_set_variable(engine, player):
    engine.execute_action("set_variable", ["name:jimmy"])
    assert player.game_variables.get("name") == "jimmy"


def test_set_variables_same_key(engine, player):
    engine.execute_action("set_variable", ["name:jimmy", "name:saul"])
    assert player.game_variables.get("name") == "saul"


def test_set_variables_different_key(engine, player):
    engine.execute_action("set_variable", ["first:jimmy", "last:saul"])
    assert player.game_variables.get("first") == "jimmy"
    assert player.game_variables.get("last") == "saul"


@pytest.mark.parametrize(
    "key",
    [
        pytest.param("name", id="single-missing"),
        pytest.param("first", id="multiple-missing-first"),
    ],
)
def test_clear_variable_not_exist(engine, player, key):
    engine.execute_action("clear_variable", [key])
    assert player.game_variables.get(key) is None


def test_clear_variable_exist(engine, player):
    engine.execute_action("set_variable", ["name:jimmy"])
    engine.execute_action("clear_variable", ["name"])
    assert player.game_variables.get("name") is None


def test_clear_multiple_variables(engine, player):
    engine.execute_action("set_variable", ["first:jimmy", "last:saul"])
    engine.execute_action("clear_variable", ["first", "last"])
    assert player.game_variables.get("first") is None
    assert player.game_variables.get("last") is None


def test_copy_variable(engine, player):
    engine.execute_action("set_variable", ["name:jeff"])
    engine.execute_action("copy_variable", ["friend", "name"])
    assert player.game_variables.get("friend") == "jeff"


@pytest.mark.parametrize(
    "fmt, expected",
    [
        pytest.param("float", 69.0, id="float"),
        pytest.param("int", 69, id="int"),
        pytest.param("-float", -69.0, id="neg-float"),
        pytest.param("-int", -69, id="neg-int"),
    ],
)
def test_format_variable(engine, player, fmt, expected):
    engine.execute_action("set_variable", ["age:69"])
    engine.execute_action("format_variable", ["age", fmt])
    assert player.game_variables.get("age") == expected


def test_format_variable_wrong_format(engine, player):
    engine.execute_action("set_variable", ["age:69"])
    with pytest.raises(ValueError):
        engine.execute_action("format_variable", ["age", "jimmy"])


def test_random_integer(engine, player):
    engine.execute_action("random_integer", ["lucky", 1, 5])
    engine.execute_action("format_variable", ["lucky", "int"])
    assert 1 <= player.game_variables.get("lucky") <= 5


def test_set_random_variable(engine, player):
    engine.execute_action(
        "set_random_variable", ["choice", "rockitten:agnite"]
    )
    assert player.game_variables.get("choice") in ["rockitten", "agnite"]


def test_variable_math_sum(engine, player):
    engine.execute_action("set_variable", ["age:69"])
    engine.execute_action("random_integer", ["lucky", 1, 5])
    engine.execute_action("variable_math", ["age", "+", "lucky", "result"])
    assert 70 <= player.game_variables.get("result") <= 74


def test_variable_math_subtraction(engine, player):
    engine.execute_action("set_variable", ["age:69"])
    engine.execute_action("random_integer", ["lucky", 1, 5])

    engine.execute_action("variable_math", ["lucky", "-", "age", "result"])
    assert -68 <= player.game_variables.get("result") <= -64

    engine.execute_action("variable_math", ["age", "-", "lucky", "result"])
    assert 64 <= player.game_variables.get("result") <= 68


def test_variable_math_division(engine, player):
    engine.execute_action("set_variable", ["age:69"])
    engine.execute_action("random_integer", ["lucky", 1, 5])
    engine.execute_action("variable_math", ["age", "/", "lucky", "result"])
    assert player.game_variables.get("result") in [69, 34, 23, 17, 13]


def test_variable_math_multiplication(engine, player):
    engine.execute_action("set_variable", ["age:69"])
    engine.execute_action("random_integer", ["lucky", 1, 5])
    engine.execute_action("variable_math", ["age", "*", "lucky", "result"])
    assert player.game_variables.get("result") in [69, 138, 207, 276, 345]


# ---------------------------------------------------------------------------
# Character Actions
# ---------------------------------------------------------------------------


def test_char_speed_between_limits(engine, player):
    player.mover.walking()
    engine.execute_action("char_speed", ["player", 6.9])
    assert player.moverate == 6.9


def test_char_speed_outside_limits(engine, player):
    lower, upper = MOVERATE_RANGE
    with pytest.raises(ValueError):
        engine.execute_action("char_speed", ["player", lower - 1])
    with pytest.raises(ValueError):
        engine.execute_action("char_speed", ["player", upper + 1])


def test_char_walk(engine, player):
    player.set_moverate(6.9)
    player.body.velocity = Vector2(1, 0)
    engine.execute_action("char_walk", ["player"])
    assert player.moverate == CONFIG.player_walkrate


def test_char_run(engine, player):
    player.set_moverate(6.9)
    player.body.velocity = Vector2(1, 0)
    engine.execute_action("char_run", ["player"])
    assert player.moverate == CONFIG.player_runrate
