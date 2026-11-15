# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random
from unittest.mock import MagicMock

import pytest

from tuxemon.database.rules import config_combat
from tuxemon.formula import speed_monster
from tuxemon.monster.monster import Monster
from tuxemon.technique.technique import Technique


@pytest.fixture
def make_monster():
    def _make(speed, dodge):
        from tuxemon.monster.stats import BasicStats
        m = MagicMock(spec=Monster)
        m.get_combat_stats.return_value = BasicStats(speed=int(speed), dodge=int(dodge))
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
    "speed,dodge,tech_speed,n,description",
    [
        pytest.param(
            10.0, 5.0, 2, 1000, "normal_case_small", id="normal_case_small"
        ),
        pytest.param(
            10.0, 5.0, 2, 10000, "normal_case_large", id="normal_case_large"
        ),
        pytest.param(
            10.0, 5.0, 0, 1000, "zero_technique", id="zero_technique"
        ),
        pytest.param(0.0, 5.0, 2, 1000, "zero_speed", id="zero_speed"),
        pytest.param(10.0, 0.0, 2, 1000, "zero_dodge", id="zero_dodge"),
        pytest.param(
            -3.0, 5.0, 2, 1000, "negative_speed", id="negative_speed"
        ),
        pytest.param(
            10.0, -3.0, 2, 1000, "negative_dodge", id="negative_dodge"
        ),
        pytest.param(
            10.0, 5.0, -3, 1000, "negative_technique", id="negative_technique"
        ),
        pytest.param(3.0, 3.0, 3, 1000, "max_values", id="max_values"),
        pytest.param(-3.0, -3.0, -3, 1000, "min_values", id="min_values"),
    ],
)
def test_speed_modifier_bounds(
    make_monster,
    make_technique,
    combat_config,
    speed,
    dodge,
    tech_speed,
    n,
    description,
):
    monster = make_monster(speed, dodge)
    technique = make_technique(tech_speed)
    results = run_speed(monster, technique, n=n)

    assert min(results) >= 1, f"Speed below minimum for {description}"

    if speed >= 0 and dodge >= 0 and tech_speed >= 0:
        max_expected = (
            speed
            * (
                combat_config.base_speed_bonus
                + technique.speed * combat_config.speed_factor
            )
            + dodge * combat_config.dodge_modifier
            + combat_config.speed_offset
        )
        assert max(results) <= max_expected, (
            f"Speed exceeds maximum for {description}"
        )


@pytest.mark.parametrize(
    "m1,m2,tech_speed,relation,n,description",
    [
        pytest.param(
            (10.0, 5.0),
            (15.0, 3.0),
            2,
            "less_equal",
            1000,
            "monster2_faster",
            id="monster2_faster",
        ),
        pytest.param(
            (10.0, 5.0),
            (20.0, 5.0),
            2,
            "less",
            1000,
            "monster3_faster",
            id="monster3_faster",
        ),
        pytest.param(
            (10.0, 5.0),
            (10.0, 10.0),
            2,
            "less",
            10000,
            "monster4_dodge",
            id="monster4_dodge",
        ),
        pytest.param(
            (10.0, 5.0),
            (1e6, 1.0),
            2,
            "less",
            1000,
            "monster5_extreme",
            id="monster5_extreme",
        ),
        pytest.param(
            (10.0, 5.0),
            (10.0, 5.0),
            2,
            "approx_equal",
            1000,
            "monster6_equal",
            id="monster6_equal",
        ),
    ],
)
def test_monster_comparisons(
    make_monster, make_technique, m1, m2, tech_speed, relation, n, description
):
    """Test speed calculations for different monster stat combinations."""
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
    "stats_pair,n,description",
    [
        pytest.param((10.0, 5.0), 1000, "monster1_small", id="monster1_small"),
        pytest.param(
            (15.0, 3.0), 10000, "monster2_large", id="monster2_large"
        ),
    ],
)
def test_fast_vs_normal_technique(
    make_monster, make_technique, stats_pair, n, description
):
    """Test that fast technique produces higher speed than normal technique."""
    random.seed(69)
    monster = make_monster(*stats_pair)
    fast = make_technique(2)
    normal = make_technique(0)

    r_fast = run_speed(monster, fast, n=n)
    r_norm = run_speed(monster, normal, n=n)

    assert sum(r_fast) / len(r_fast) > sum(r_norm) / len(r_norm)


def test_random_offset_with_large_speed_offset(make_monster, make_technique):
    from tuxemon.monster.stats import BasicStats

    monster = MagicMock(spec=Monster)
    monster.get_combat_stats.return_value = BasicStats(speed=10, dodge=0)
    technique = make_technique(1)
    config_combat.speed_offset = 1000
    results = run_speed(monster, technique, n=1000)
    assert all(r >= 1 for r in results)


def test_min_speed_modifier_reset(make_monster, make_technique):
    from tuxemon.monster.stats import BasicStats

    monster = MagicMock(spec=Monster)
    monster.get_combat_stats.return_value = BasicStats(speed=0, dodge=0)
    technique = make_technique(0)
    config_combat.min_speed_modifier = 0
    result = speed_monster(monster, technique)
    assert result >= 1
    assert config_combat.min_speed_modifier == 0


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


def test_speed_monster_does_not_mutate_config(make_monster, make_technique):
    monster = make_monster(0, 0)
    technique = make_technique(0)
    config_combat.min_speed_modifier = 0
    before = config_combat.min_speed_modifier
    speed_monster(monster, technique)
    assert config_combat.min_speed_modifier == before
