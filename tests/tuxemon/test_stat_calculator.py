# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.database.rules import config_monster
from tuxemon.monster.stats import (
    BasicStats,
    CustomStatBoosts,
    IndividualValues,
    StatAnalyzer,
    StatCalculator,
    TrainingPoints,
)
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
    warm = MagicMock(spec=Taste)

    cold.modifiers = [
        MagicMock(values=["speed"], multiplier=1.2),
        MagicMock(values=["hp"], multiplier=0.9),
    ]
    warm.modifiers = [
        MagicMock(values=["melee"], multiplier=1.1),
    ]

    def get_multiplier(taste, stat_name: str) -> float:
        m = 1.0
        for mod in taste.modifiers:
            if stat_name in mod.values:
                m *= mod.multiplier
        return m

    def apply_to_stat(taste, stat_name: str, value: int) -> int:
        return round(value * get_multiplier(taste, stat_name))

    cold.get_multiplier.side_effect = lambda stat: get_multiplier(cold, stat)
    warm.get_multiplier.side_effect = lambda stat: get_multiplier(warm, stat)

    cold.apply_to_stat.side_effect = lambda stat, val: apply_to_stat(
        cold, stat, val
    )
    warm.apply_to_stat.side_effect = lambda stat, val: apply_to_stat(
        warm, stat, val
    )

    Taste.get = MagicMock(
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
    individual_values = IndividualValues()
    return StatCalculator(
        base_stats=base_stats,
        level=5,
        shape=mock_shape,
        taste_cold="cold",
        taste_warm="warm",
        custom_stats=custom_stats,
        training_points=training_points,
        individual_values=individual_values,
    )


@pytest.fixture
def analyzer(calculator):
    return StatAnalyzer(calculator)


# StatCalculator tests
def test_apply_base_stat_calculation(calculator):
    level = calculator.level
    multiplier = level + config_monster.coeff_stats
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
        pytest.param("hp", 100, int(100 * 0.9), id="hp_mod"),
        pytest.param("speed", 30, int(30 * 1.2), id="speed_mod"),
        pytest.param("melee", 20, int(20 * 1.1), id="melee_mod"),
        pytest.param("armour", 10, 10, id="armour_no_mod"),
        pytest.param("dodge", 10, 10, id="dodge_no_mod"),
        pytest.param("ranged", 5, 5, id="ranged_no_mod"),
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
        pytest.param("speed", 50, 1.2, id="speed_update"),
        pytest.param("melee", 40, 1.1, id="melee_update"),
        pytest.param("armour", 20, 1.0, id="armour_no_update"),
    ],
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
    assert stats.armour == (2 * (50 + config_monster.coeff_stats)) + 50 + 1


def test_negative_modifier(calculator):
    calculator.custom_stats.hp = -10
    stats = calculator.calculate_raw_stats(level=calculator.level)
    assert stats.hp < (5 * (calculator.level + config_monster.coeff_stats))


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


# TrainingPoints invariant tests


def test_tp_validate_individual_clamp():
    tp = TrainingPoints(armour=config_monster.max_tps + 50)
    tp.validate()
    assert tp.armour == config_monster.max_tps


def test_tp_validate_total_clamp_proportional():
    tp = TrainingPoints(
        armour=200, dodge=200, hp=200, melee=200, ranged=200, speed=200
    )
    tp.validate()
    total_after = tp.sum()
    assert total_after <= config_monster.max_total_tps
    assert pytest.approx(tp.armour, rel=0.1) == tp.dodge
    assert pytest.approx(tp.armour, rel=0.1) == tp.hp


def test_tp_validate_no_change_when_valid():
    tp = TrainingPoints(armour=10, dodge=5, hp=3, melee=2, ranged=1, speed=4)
    before = tp.to_dict().copy()
    tp.validate()
    assert tp.to_dict() == before


def test_tp_validate_individual_then_total():
    tp = TrainingPoints(
        armour=config_monster.max_tps + 20,
        dodge=config_monster.max_tps + 10,
        hp=50,
        melee=50,
        ranged=50,
        speed=50,
    )
    tp.validate()
    assert tp.armour <= config_monster.max_tps
    assert tp.dodge <= config_monster.max_tps
    assert tp.sum() <= config_monster.max_total_tps


def test_tp_validate_scaling_preserves_zero_stats():
    tp = TrainingPoints(
        armour=100,
        dodge=0,
        hp=100,
        melee=0,
        ranged=100,
        speed=0,
    )
    tp.validate()
    assert tp.dodge == 0
    assert tp.melee == 0
    assert tp.speed == 0
