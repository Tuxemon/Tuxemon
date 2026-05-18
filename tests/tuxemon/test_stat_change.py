# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random
from unittest.mock import patch

import pytest

from tuxemon.db import StatModel
from tuxemon.monster.stat_utils import apply_stat_modifiers
from tuxemon.monster.stats import BasicStats


class DummyMonster:
    def __init__(self):
        self.base_stats = BasicStats(
            armour=10, dodge=5, hp=100, melee=20, ranged=15, speed=30
        )
        self.current_hp = 80
        self.hp = self.base_stats.hp

    def return_stat(self, stat_type):
        return getattr(self.base_stats, stat_type)


class DummySource:
    def __init__(self):
        self.temporary_stat_boosts = BasicStats()


@pytest.fixture
def monster():
    return DummyMonster()


@pytest.fixture
def source():
    return DummySource()


ALL_STATS = ["armour", "dodge", "melee", "ranged", "speed", "hp"]


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"nonlinear_step_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=2)
def test_step_based_nonlinear_all_stats(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=2, max_deviation=0, scaling_mode="nonlinear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 2
    expected_new_value = int(base * 2.0)
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"value_add_{s}") for s in ALL_STATS],
)
def test_value_based_add_all_stats(monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(
            value=5, step=None, operation="+", max_deviation=0
        )
    }
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, stat_slug) == 5


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"negative_clamp_{s}") for s in ALL_STATS],
)
def test_negative_value_clamped_all_stats(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    modifiers = {stat_slug: StatModel(value=-999, step=None, operation="+")}
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, stat_slug) == 1 - base


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"step_clamp_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=999)
def test_step_clamping_all_stats(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(
            step=6, max_deviation=10, scaling_mode="nonlinear"
        )
    }
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 6


def test_hp_override(monster, source):
    modifiers = {"current_hp": StatModel(overridetofull=True)}
    apply_stat_modifiers(monster, source, modifiers)
    assert monster.current_hp == monster.base_stats.hp


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_step_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=2)
def test_step_based_linear_all_stats(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=2, max_deviation=0, scaling_mode="linear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 2
    multiplier = 1 + (2 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_negative_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=-3)
def test_step_based_linear_negative(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=-3, max_deviation=0, scaling_mode="linear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == -3
    multiplier = 1 + (-3 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_dev_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=5)
def test_step_based_linear_with_deviation(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=2, max_deviation=10, scaling_mode="linear")
    }
    base = getattr(monster.base_stats, stat_slug)
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 5
    multiplier = 1 + (5 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"linear_clamp_{s}") for s in ALL_STATS],
)
@patch("random.randint", return_value=999)
def test_step_based_linear_clamping(_, monster, source, stat_slug):
    modifiers = {
        stat_slug: StatModel(step=6, max_deviation=10, scaling_mode="linear")
    }
    apply_stat_modifiers(monster, source, modifiers)
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 6


@patch("random.randint", return_value=2)
def test_step_based_linear_hp(_, monster, source):
    modifiers = {
        "hp": StatModel(step=2, max_deviation=0, scaling_mode="linear")
    }
    base = monster.base_stats.hp
    apply_stat_modifiers(monster, source, modifiers)
    assert source.temporary_stat_boosts.hp_stage == 2
    multiplier = 1 + (2 / 6)
    expected_new_value = int(base * multiplier)
    expected_boost = expected_new_value - base
    assert source.temporary_stat_boosts.hp == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_pos_{s}") for s in ALL_STATS],
)
def test_stacking_positive(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    with patch("random.randint", return_value=2):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=2, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=3):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=3, scaling_mode="nonlinear")},
        )
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 5
    expected_new_value = int(base * (7 / 2))
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_neg_{s}") for s in ALL_STATS],
)
def test_stacking_negative(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    with patch("random.randint", return_value=-2):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-2, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=-3):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-3, scaling_mode="nonlinear")},
        )
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == -5
    expected_new_value = int(base * (2 / 7))
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_mix_{s}") for s in ALL_STATS],
)
def test_stacking_mixed(monster, source, stat_slug):
    base = getattr(monster.base_stats, stat_slug)
    with patch("random.randint", return_value=4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=4, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=-3):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-3, scaling_mode="nonlinear")},
        )
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 1
    expected_new_value = int(base * (3 / 2))
    expected_boost = expected_new_value - base
    assert getattr(source.temporary_stat_boosts, stat_slug) == expected_boost


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_clamp_{s}") for s in ALL_STATS],
)
def test_stacking_clamping(monster, source, stat_slug):
    with patch("random.randint", return_value=4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=4, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=4, scaling_mode="nonlinear")},
        )
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 6


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"stack_clamp_neg_{s}") for s in ALL_STATS],
)
def test_stacking_clamping_negative(monster, source, stat_slug):
    with patch("random.randint", return_value=-4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-4, scaling_mode="nonlinear")},
        )
    with patch("random.randint", return_value=-4):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=-4, scaling_mode="nonlinear")},
        )
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == -6


@pytest.mark.parametrize(
    "stat_slug",
    [pytest.param(s, id=f"reset_{s}") for s in ALL_STATS],
)
def test_reset_cleanup(monster, source, stat_slug):
    with patch("random.randint", return_value=2):
        apply_stat_modifiers(
            monster,
            source,
            {stat_slug: StatModel(step=2, scaling_mode="nonlinear")},
        )
    assert getattr(source.temporary_stat_boosts, f"{stat_slug}_stage") == 2
    source.temporary_stat_boosts = BasicStats()
    for s in ALL_STATS:
        assert getattr(source.temporary_stat_boosts, s) == 0
    for s in ALL_STATS:
        assert not hasattr(source.temporary_stat_boosts, f"{s}_stage")


def test_stress_100_random(monster, source):
    for _ in range(100):
        stat_slug = random.choice(ALL_STATS)
        if random.random() < 0.7:
            step = random.randint(-6, 6)
            max_dev = random.randint(0, 3)
            scaling_mode = random.choice(["linear", "nonlinear"])
            model = StatModel(
                step=step, max_deviation=max_dev, scaling_mode=scaling_mode
            )
        else:
            value = random.randint(-20, 20)
            max_dev = random.randint(0, 5)
            op = random.choice(["+", "-", "*", "/"])
            model = StatModel(
                value=value, step=None, max_deviation=max_dev, operation=op
            )

        apply_stat_modifiers(monster, source, {stat_slug: model})

        stage_attr = f"{stat_slug}_stage"
        if hasattr(source.temporary_stat_boosts, stage_attr):
            stage = getattr(source.temporary_stat_boosts, stage_attr)
            assert -6 <= stage <= 6

        if stat_slug != "current_hp":
            boost = getattr(source.temporary_stat_boosts, stat_slug)
            base = getattr(monster.base_stats, stat_slug)
            assert base + boost >= 1

        assert 0 <= monster.current_hp <= monster.base_stats.hp
