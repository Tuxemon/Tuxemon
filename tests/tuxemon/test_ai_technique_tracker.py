# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.ai.technique_tracker import (
    TechniqueScoreResult,
    TechniqueTracker,
    technique_score,
)
from tuxemon.database.rules import config_combat
from tuxemon.element import ElementTypesHandler


@pytest.fixture(autouse=True)
def clear_multiplier_cache():
    """The multiplier cache is keyed by slug pair and leaks across tests."""
    ElementTypesHandler.clear_cache()
    yield
    ElementTypesHandler.clear_cache()


@pytest.fixture
def mock_config():
    return MagicMock(
        elemental_multiplier_weight=1.0,
        elemental_health_threshold=0.5,
        elemental_health_scaling=2.0,
        melee_bonus=1.0,
        power_weight=1.0,
        accuracy_weight=1.0,
        health_priority_threshold=0.3,
        healing_penalty_threshold=0.7,
        healing_weight=1.0,
        healing_penalty_weight=1.0,
    )


@pytest.fixture
def mock_user():
    return MagicMock(hp_ratio=0.2, hp=100, current_hp=20)


@pytest.fixture
def healing_technique():
    tech = MagicMock(
        slug="heal",
        range="melee",
        power=0.0,
        accuracy=1.0,
        healing_power=10.0,
    )
    type_obj = MagicMock(slug="normal")
    type_obj.lookup_multiplier.return_value = 1.0
    tech.types.current = [type_obj]
    return tech


@pytest.fixture
def mock_opponent():
    opp = MagicMock()
    opp.hp = 100
    opp.current_hp = 50
    type_obj = MagicMock(slug="normal")
    type_obj.lookup_multiplier.return_value = 1.0
    opp.types.current = [type_obj]
    opp.held_item = None
    return opp


@pytest.fixture
def mock_technique():
    tech = MagicMock(
        slug="fireball",
        range="melee",
        power=50,
        accuracy=0.8,
        healing_power=0.0,
        is_recharging=False,
    )
    type_obj = MagicMock(slug="fire")
    type_obj.lookup_multiplier.return_value = 1.0
    tech.types.current = [type_obj]
    return tech


def test_technique_score_breakdown(
    mock_user, mock_opponent, mock_technique, mock_config
):
    result = technique_score(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    assert isinstance(result, TechniqueScoreResult)
    assert pytest.approx(result.total, 0.01) == sum(result.breakdown.values())
    for key in ["effectiveness", "type_bonus", "power", "accuracy", "healing"]:
        assert key in result.breakdown


def test_evaluate_technique_logs(
    mock_user, mock_opponent, mock_technique, mock_config, caplog
):
    tracker = TechniqueTracker(session=MagicMock(), moves=[mock_technique])
    with caplog.at_level("DEBUG"):
        score = tracker.evaluate_technique(
            mock_user, mock_technique, mock_opponent, mock_config
        )

    assert isinstance(score, float)
    assert "Technique evaluation for fireball" in caplog.text
    assert "Final technique score" in caplog.text


def test_get_valid_moves_filters_recharging_and_invalid():
    session = MagicMock()
    valid_tech = MagicMock(is_recharging=False)
    valid_tech.validate_monster.return_value = True
    valid_tech.can_use.return_value = True
    invalid_tech = MagicMock(is_recharging=True)
    invalid_tech.can_use.return_value = False
    tracker = TechniqueTracker(session, [valid_tech, invalid_tech])
    opponent = MagicMock()
    moves = tracker.get_valid_moves([opponent])
    assert all(mov[0] is valid_tech for mov in moves)
    assert invalid_tech not in [m[0] for m in moves]


def test_healing_positive_when_low_hp(
    mock_config, healing_technique, mock_opponent
):
    user = MagicMock(hp_ratio=0.2)
    result = technique_score(
        user, healing_technique, mock_opponent, mock_config
    )
    assert isinstance(result, TechniqueScoreResult)
    assert result.breakdown["healing"] > 0
    assert result.total == pytest.approx(sum(result.breakdown.values()), 0.01)


def test_healing_negative_when_high_hp(
    mock_config, healing_technique, mock_opponent
):
    user = MagicMock(hp_ratio=0.8)
    result = technique_score(
        user, healing_technique, mock_opponent, mock_config
    )
    assert isinstance(result, TechniqueScoreResult)
    assert result.breakdown["healing"] < 0
    assert result.total == pytest.approx(sum(result.breakdown.values()), 0.01)


# Held item (element mantle) resistance


def _mantle(resistances):
    return MagicMock(element_resistances=resistances)


def _effectiveness(user, technique, opponent, config):
    ElementTypesHandler.clear_cache()
    return technique_score(user, technique, opponent, config).breakdown[
        "effectiveness"
    ]


def test_matching_mantle_lowers_effectiveness(
    mock_user, mock_opponent, mock_technique, mock_config
):
    plain = _effectiveness(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    mock_opponent.held_item = _mantle({"fire": 0.5})
    resisted = _effectiveness(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    assert resisted == pytest.approx(plain * 0.5)


def test_non_matching_mantle_keeps_effectiveness(
    mock_user, mock_opponent, mock_technique, mock_config
):
    plain = _effectiveness(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    mock_opponent.held_item = _mantle({"water": 0.5})
    other = _effectiveness(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    assert other == pytest.approx(plain)


def test_mantle_cancels_super_effective_advantage(
    mock_user, mock_opponent, mock_technique, mock_config
):
    mock_technique.types.current[0].lookup_multiplier.return_value = 2.0
    mock_config.elemental_health_threshold = None
    mock_opponent.held_item = _mantle({"fire": 0.5})
    result = technique_score(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    assert result.breakdown["effectiveness"] == pytest.approx(
        1.0 * mock_config.elemental_multiplier_weight
    )


def test_mantle_effectiveness_clamped_to_minimum(
    mock_user, mock_opponent, mock_technique, mock_config
):
    min_range, _ = config_combat.multiplier_range
    mock_technique.types.current[0].lookup_multiplier.return_value = min_range
    mock_config.elemental_health_threshold = None
    mock_opponent.held_item = _mantle({"fire": 0.5})
    result = technique_score(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    assert result.breakdown["effectiveness"] == pytest.approx(
        min_range * mock_config.elemental_multiplier_weight
    )


def test_ai_prefers_unresisted_technique(
    mock_user, mock_opponent, mock_technique, mock_config
):
    """
    With otherwise identical techniques, the AI should score the one the
    opponent's mantle does not resist higher.
    """
    water_tech = MagicMock(
        slug="splash",
        range="melee",
        power=mock_technique.power,
        accuracy=mock_technique.accuracy,
        healing_power=0.0,
    )
    water_type = MagicMock(slug="water")
    water_type.lookup_multiplier.return_value = 1.0
    water_tech.types.current = [water_type]

    mock_opponent.held_item = _mantle({"fire": 0.5})
    fire_score = technique_score(
        mock_user, mock_technique, mock_opponent, mock_config
    ).total
    water_score = technique_score(
        mock_user, water_tech, mock_opponent, mock_config
    ).total
    assert water_score > fire_score


def test_mantle_ignored_when_weight_disabled(
    mock_user, mock_opponent, mock_technique, mock_config
):
    mock_config.elemental_multiplier_weight = 0.0
    mock_opponent.held_item = _mantle({"fire": 0.5})
    result = technique_score(
        mock_user, mock_technique, mock_opponent, mock_config
    )
    assert result.breakdown["effectiveness"] == 0.0
