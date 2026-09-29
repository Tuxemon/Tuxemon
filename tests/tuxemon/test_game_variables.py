# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.db import GameCondition
from tuxemon.game_variables import GameVariablesManager


@pytest.fixture
def manager():
    return GameVariablesManager(
        initial_player={"hp": 10, "daytime": True},
        initial_world={"weather": "rain", "difficulty": 2},
    )


def test_scope_basic_operations(manager):
    assert manager.player.get("hp") == 10
    assert manager.world.get("weather") == "rain"

    manager.player.set("hp", 20)
    assert manager.player.get("hp") == 20

    assert manager.player.has("hp")
    assert not manager.player.has("missing")

    assert manager.world.remove("weather")
    assert not manager.world.has("weather")


def test_dirty_flags(manager):
    assert not manager.is_any_dirty()

    manager.player.set("hp", 99)
    assert manager.is_any_dirty()

    manager.clear_all_dirty()
    assert not manager.is_any_dirty()

    manager.world.set("difficulty", 5)
    assert manager.is_any_dirty()


@pytest.mark.parametrize(
    "key, expected",
    [
        pytest.param("hp", 10, id="resolve_hp"),
        pytest.param("daytime", True, id="resolve_daytime"),
        pytest.param("weather", "rain", id="resolve_weather"),
        pytest.param("difficulty", 2, id="resolve_difficulty"),
        pytest.param("missing", None, id="resolve_missing"),
    ],
)
def test_resolve_value(manager, key, expected):
    assert manager._resolve_value(key) == expected


@pytest.mark.parametrize(
    "conditions, expected",
    [
        pytest.param([{"hp": 10}], True, id="dict_hp_match"),
        pytest.param([{"hp": 5}], False, id="dict_hp_mismatch"),
        pytest.param([{"weather": "rain"}], True, id="dict_weather_match"),
        pytest.param([{"weather": "sun"}], False, id="dict_weather_mismatch"),
        pytest.param(
            [{"hp": 10}, {"weather": "rain"}], True, id="dict_multi_match"
        ),
        pytest.param(
            [{"hp": 10}, {"weather": "sun"}],
            False,
            id="dict_multi_partial_mismatch",
        ),
        pytest.param([], True, id="dict_empty_true"),
    ],
)
def test_check_logic_dict(manager, conditions, expected):
    assert manager.check_logic(conditions) is expected


@pytest.mark.parametrize(
    "conditions, expected",
    [
        pytest.param(
            [GameCondition(key="hp", value=10)], True, id="cond_hp_match"
        ),
        pytest.param(
            [GameCondition(key="hp", value=5)], False, id="cond_hp_mismatch"
        ),
        pytest.param(
            [GameCondition(key="weather", value="rain")],
            True,
            id="cond_weather_match",
        ),
        pytest.param(
            [GameCondition(key="weather", value="sun")],
            False,
            id="cond_weather_mismatch",
        ),
        pytest.param(
            [
                GameCondition(key="hp", value=10),
                GameCondition(key="weather", value="rain"),
            ],
            True,
            id="cond_multi_match",
        ),
        pytest.param(
            [
                GameCondition(key="hp", value=10),
                GameCondition(key="weather", value="sun"),
            ],
            False,
            id="cond_multi_partial_mismatch",
        ),
        pytest.param([], True, id="cond_empty_true"),
    ],
)
def test_check_conditions(manager, conditions, expected):
    assert manager.check_conditions(conditions) is expected


@pytest.mark.parametrize(
    "cond, expected",
    [
        pytest.param(
            GameCondition(key="hp", value=10, scope="player"),
            True,
            id="scope_player_match",
        ),
        pytest.param(
            GameCondition(key="hp", value=10, scope="world"),
            False,
            id="scope_world_mismatch",
        ),
        pytest.param(
            GameCondition(key="weather", value="rain", scope="world"),
            True,
            id="scope_world_match",
        ),
        pytest.param(
            GameCondition(key="weather", value="rain", scope="player"),
            False,
            id="scope_player_mismatch",
        ),
    ],
)
def test_check_conditions_scope(manager, cond, expected):
    assert manager.check_conditions([cond]) is expected


def test_missing_requirements(manager):
    conditions = [
        GameCondition(key="hp", value=10, description="HP must be 10"),
        GameCondition(key="weather", value="sun", description="Sunny weather"),
        GameCondition(key="difficulty", value=2),
    ]

    missing = manager.get_missing_requirements(conditions)

    assert "Sunny weather" in missing
    assert "Missing requirement: difficulty" not in missing
    assert len(missing) == 1


def test_missing_requirements_empty(manager):
    assert manager.get_missing_requirements([]) == []


def test_check_logic_unknown_key(manager):
    assert not manager.check_logic([{"unknown": 5}])


def test_check_conditions_unknown_key(manager):
    cond = GameCondition(key="unknown", value=123)
    assert not manager.check_conditions([cond])


def test_numeric_comparison(manager):
    manager.player.set("score", 100)
    cond = GameCondition(key="score", value=100)
    assert manager.check_conditions([cond])


def test_none_values(manager):
    manager.player.set("flag", None)
    cond = GameCondition(key="flag", value=None)
    assert manager.check_conditions([cond])
