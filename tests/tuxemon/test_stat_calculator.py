# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.monster_dir.stats import (
    BasicStats,
    CustomStatBoosts,
    StatAnalyzer,
    StatCalculator,
    TrainingPoints,
)
from tuxemon.prepare import COEFF_STATS
from tuxemon.shape import ShapeHandler
from tuxemon.taste import Taste


@pytest.fixture
def mock_shape():
    shape = MagicMock(spec=ShapeHandler)
    shape.attributes = BasicStats(
        armour=2, dodge=3, hp=5, melee=4, ranged=1, speed=2
    )
    return shape


@pytest.fixture
def mock_tastes():
    cold = MagicMock(spec=Taste)
    cold.slug = "cold"
    cold.modifiers = [
        MagicMock(values=["speed"], multiplier=1.2),
        MagicMock(values=["hp"], multiplier=0.9),
    ]
    warm = MagicMock(spec=Taste)
    warm.slug = "warm"
    warm.modifiers = [MagicMock(values=["melee"], multiplier=1.1)]
    Taste.get_taste = MagicMock(
        side_effect=lambda name: {"cold": cold, "warm": warm}[name]
    )
    return cold, warm


@pytest.fixture
def calculator(mock_shape, mock_tastes):
    cold, warm = mock_tastes
    custom_stats = CustomStatBoosts(
        armour=1, dodge=0, hp=2, melee=0, ranged=0, speed=3
    )
    base_stats = BasicStats()
    training_points = TrainingPoints()
    return StatCalculator(
        base_stats=base_stats,
        level=5,
        shape=mock_shape,
        taste_cold="cold",
        taste_warm="warm",
        custom_stats=custom_stats,
        training_points=training_points,
    )


@pytest.fixture
def analyzer(calculator):
    return StatAnalyzer(calculator)


# StatCalculator tests
def test_apply_base_stat_calculation(calculator):
    level = calculator.level
    multiplier = level + COEFF_STATS
    stats = calculator.calculate_raw_stats(level=level)
    assert stats.armour == 2 * multiplier + 1
    assert stats.dodge == 3 * multiplier + 0
    assert stats.hp == 5 * multiplier + 2
    assert stats.melee == 4 * multiplier + 0
    assert stats.ranged == 1 * multiplier + 0
    assert stats.speed == 2 * multiplier + 3


@pytest.mark.parametrize(
    "stat, value, expected",
    [
        ("hp", 100, int(100 * 0.9)),
        ("speed", 30, int(30 * 1.2)),
        ("melee", 20, int(20 * 1.1)),
        ("armour", 10, 10),
        ("dodge", 10, 10),
        ("ranged", 5, 5),
    ],
    ids=[
        "hp_mod",
        "speed_mod",
        "melee_mod",
        "armour_no_mod",
        "dodge_no_mod",
        "ranged_no_mod",
    ],
)
def test_apply_stat_updates(calculator, mock_tastes, stat, value, expected):
    cold, warm = mock_tastes
    base_stats = BasicStats(
        armour=10, dodge=10, hp=100, melee=20, ranged=5, speed=30
    )
    updated = calculator.apply_stat_updates(base_stats, cold, warm)
    assert getattr(updated, stat) == expected


@pytest.mark.parametrize(
    "stat, value, expected_multiplier",
    [
        ("speed", 50, 1.2),
        ("melee", 40, 1.1),
        ("armour", 20, 1.0),
    ],
    ids=["speed_update", "melee_update", "armour_no_update"],
)
def test_update_stat(
    calculator, mock_tastes, stat, value, expected_multiplier
):
    cold, warm = mock_tastes
    result = calculator.update_stat(stat, value, cold, warm)
    assert result == int(value * expected_multiplier)


def test_calculate(calculator):
    final_stats = calculator.calculate()
    assert isinstance(final_stats, BasicStats)
    assert final_stats.sum() > 0


def test_calculate_at_level(calculator):
    stats = calculator.calculate_at_level(10)
    assert isinstance(stats, BasicStats)
    assert stats.sum() > 0


def test_calculate_at_level_invalid(calculator):
    with pytest.raises(ValueError):
        calculator.calculate_at_level(0)


def test_training_point_scaling(calculator):
    calculator.training_points.armour = 100
    stats = calculator.calculate_raw_stats(level=50)
    assert stats.armour == (2 * (50 + COEFF_STATS)) + 50 + 1


def test_negative_modifier(calculator):
    calculator.custom_stats.hp = -10
    stats = calculator.calculate_raw_stats(level=calculator.level)
    assert stats.hp < (5 * (calculator.level + COEFF_STATS))


def test_high_level_scaling(calculator):
    stats = calculator.calculate_raw_stats(level=1000)
    assert stats.sum() > 0


# StatAnalyzer tests
def test_get_breakdown_structure(analyzer):
    breakdown = analyzer.get_breakdown()
    assert set(breakdown.keys()) == set(BasicStats.names())
    for details in breakdown.values():
        for key in [
            "base_value",
            "training_points_raw",
            "training_points_scaled",
            "temporary_modifier",
            "pre_taste_total",
            "taste_multiplier",
            "final_value",
        ]:
            assert key in details


def test_evaluate_taste_efficiency(analyzer):
    score = analyzer.evaluate_taste_efficiency()
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0


def test_get_stat_growth_curve(analyzer):
    curve = analyzer.get_stat_growth_curve(3)
    assert len(curve) == 3
    for level, stats in curve.items():
        assert isinstance(level, int)
        assert isinstance(stats, BasicStats)
        assert stats.sum() > 0


def test_get_stat_growth_curve_invalid(analyzer):
    with pytest.raises(ValueError):
        analyzer.get_stat_growth_curve(0)


def test_growth_curve_monotonic(analyzer):
    curve = analyzer.get_stat_growth_curve(5)
    hp_values = [curve[level].hp for level in range(1, 6)]
    assert all(
        hp_values[i] <= hp_values[i + 1] for i in range(len(hp_values) - 1)
    )


def test_breakdown_matches_calculator(analyzer, calculator):
    breakdown = analyzer.get_breakdown()
    final_stats = calculator.calculate()
    for stat in BasicStats.names():
        assert breakdown[stat]["final_value"] == getattr(final_stats, stat)


def test_taste_multiplier_stacking(analyzer, mock_tastes):
    cold, warm = mock_tastes
    warm.modifiers = []
    cold.modifiers = [
        MagicMock(values=["hp"], multiplier=1.5),
        MagicMock(values=["hp"], multiplier=2.0),
    ]
    breakdown = analyzer.get_breakdown()
    assert (
        pytest.approx(breakdown["hp"]["taste_multiplier"], rel=1e-2)
        == 1.5 * 2.0
    )
