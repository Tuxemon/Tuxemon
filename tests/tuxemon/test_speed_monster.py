# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random
from unittest.mock import MagicMock

import pytest

from tuxemon.formula import config_combat, speed_monster
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


@pytest.fixture
def make_monster():
    def _make(speed, dodge):
        m = MagicMock(spec=Monster)
        m.speed = speed
        m.dodge = dodge
        return m

    return _make


@pytest.fixture
def make_technique():
    def _make(speed):
        t = MagicMock(spec=Technique)
        t.speed = speed
        return t

    return _make


@pytest.fixture
def combat_config():
    return config_combat


def run_speed(monster, technique, n=1000):
    """Helper to run speed_monster multiple times and return results."""
    return [speed_monster(monster, technique) for _ in range(n)]


@pytest.mark.parametrize(
    "speed, dodge, tech_speed",
    [
        (10.0, 5.0, 2),  # fast technique
        (10.0, 5.0, 0),  # normal technique
        (0.0, 5.0, 2),  # zero speed
        (-3.0, 5.0, 2),  # negative speed
        (10.0, 0.0, 2),  # zero dodge
        (10.0, -3.0, 2),  # negative dodge
        (10.0, 5.0, 0),  # zero technique
        (10.0, 5.0, -3),  # negative technique
        (3.0, 3.0, 3),  # max values
        (-3.0, -3.0, -3),  # min values
    ],
)
@pytest.mark.parametrize("n", [1000, 10000])
def test_speed_modifier_bounds(
    make_monster, make_technique, combat_config, speed, dodge, tech_speed, n
):
    monster = make_monster(speed, dodge)
    technique = make_technique(tech_speed)
    results = run_speed(monster, technique, n=n)

    assert min(results) >= 1

    if speed >= 0 and dodge >= 0 and tech_speed >= 0:
        assert max(results) <= (
            monster.speed
            * (
                combat_config.base_speed_bonus
                + technique.speed * combat_config.speed_factor
            )
            + monster.dodge * combat_config.dodge_modifier
            + combat_config.speed_offset
        )


@pytest.mark.parametrize(
    "m1, m2, tech_speed, relation, n",
    [
        # monster2 faster than monster1
        ((10.0, 5.0), (15.0, 3.0), 2, "less_equal", 1000),
        # monster3 faster than monster1
        ((10.0, 5.0), (20.0, 5.0), 2, "less", 1000),
        # monster4 higher dodge than monster1
        ((10.0, 5.0), (10.0, 10.0), 2, "less", 10000),
        # monster5 extreme speed vs monster1
        ((10.0, 5.0), (1e6, 1.0), 2, "less", 1000),
        # monster6 equal stats to monster1
        ((10.0, 5.0), (10.0, 5.0), 2, "approx_equal", 1000),
    ],
)
def test_monster_comparisons(
    make_monster, make_technique, m1, m2, tech_speed, relation, n
):
    monster1 = make_monster(*m1)
    monster2 = make_monster(*m2)
    technique = make_technique(tech_speed)

    r1 = run_speed(monster1, technique, n=n)
    r2 = run_speed(monster2, technique, n=n)

    avg1, avg2 = sum(r1) / len(r1), sum(r2) / len(r2)

    if relation == "less_equal":
        assert avg1 <= avg2
    elif relation == "less":
        assert avg2 >= avg1 * 0.95
    elif relation == "approx_equal":
        assert abs(avg1 - avg2) < 5


@pytest.mark.parametrize(
    "monster_stats",
    [
        (10.0, 5.0),  # monster1
        (15.0, 3.0),  # monster2
    ],
)
@pytest.mark.parametrize("n", [1000, 10000])
def test_fast_vs_normal_technique(
    make_monster, make_technique, monster_stats, n
):
    random.seed(69)
    monster = make_monster(*monster_stats)
    fast = make_technique(2)
    normal = make_technique(0)

    r_fast = run_speed(monster, fast, n=n)
    r_norm = run_speed(monster, normal, n=n)

    assert sum(r_fast) / len(r_fast) > sum(r_norm) / len(r_norm)


def test_random_offset_with_large_speed_offset(
    monster=MagicMock(spec=Monster), technique=MagicMock(spec=Technique)
):
    monster.speed = 10.0
    monster.dodge = 0.0
    technique.speed = 1
    config_combat.speed_offset = 1000
    results = run_speed(monster, technique, n=1000)
    assert all(r >= 1 for r in results)


def test_min_speed_modifier_reset(
    monster=MagicMock(spec=Monster), technique=MagicMock(spec=Technique)
):
    monster.speed = 0
    monster.dodge = 0
    technique.speed = 0
    config_combat.min_speed_modifier = 0
    result = speed_monster(monster, technique)
    assert result >= 1
    assert config_combat.min_speed_modifier == 1


def test_negative_dodge_is_clamped(make_monster, make_technique):
    monster = make_monster(10.0, -50.0)
    technique = make_technique(1)
    result = speed_monster(monster, technique)
    assert result >= 1


def test_extremely_large_speed_and_technique(make_monster, make_technique):
    monster = make_monster(1e9, 1000)
    technique = make_technique(1000)
    result = speed_monster(monster, technique)
    assert isinstance(result, int)
    assert result > 0


def test_random_seed_reproducibility(make_monster, make_technique):
    monster = make_monster(10.0, 5.0)
    technique = make_technique(2)
    random.seed(123)
    r1 = run_speed(monster, technique, n=10)
    random.seed(123)
    r2 = run_speed(monster, technique, n=10)
    assert r1 == r2
