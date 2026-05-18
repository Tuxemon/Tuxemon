# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.ai.opponent_evaluator import OpponentEvaluator, calculate_score


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.client.combat_session.is_trainer_battle = True
    session.client.combat_session.is_double = True
    return session


@pytest.fixture
def mock_user():
    user = MagicMock(slug="rockitten", level=10)
    user.get_owner.return_value = MagicMock(slug="trainer_slug")
    return user


@pytest.fixture
def mock_ai_opponent():
    ai_opponent = MagicMock()
    ai_opponent.rules = {}
    return ai_opponent


def test_evaluate_returns_one_if_not_trainer_or_double(
    mock_user, mock_ai_opponent
):
    session = MagicMock()
    session.client.combat_session.is_trainer_battle = False
    session.client.combat_session.is_double = False
    opponent = MagicMock()
    evaluator = OpponentEvaluator(
        session, mock_user, [opponent], mock_ai_opponent
    )
    assert evaluator.evaluate(opponent) == 1.0


def test_evaluate_returns_one_if_no_config(
    mock_session, mock_user, mock_ai_opponent
):
    opponent = MagicMock()
    evaluator = OpponentEvaluator(
        mock_session, mock_user, [opponent], mock_ai_opponent
    )
    # no rules configured
    evaluator.ai_opponent.rules = {}
    assert evaluator.evaluate(opponent) == 1.0


def test_calculate_score_basic():
    config = MagicMock(
        health_weight=1.0,
        armour_weight=1.0,
        dodge_weight=1.0,
        melee_weight=1.0,
        ranged_weight=1.0,
        speed_weight=1.0,
        status_effects={"poison": 2.0},
        status_effects_weight=1.0,
        level_difference_threshold=2,
        level_difference_weight=1.0,
    )
    user = MagicMock(level=10)
    opponent = MagicMock(
        hp_ratio=0.5,
        armour=2,
        dodge=3,
        melee=4,
        ranged=5,
        speed=6,
        level=13,
    )
    opponent.status.get_statuses.return_value = [MagicMock(slug="poison")]

    result = calculate_score(config, user, opponent)

    assert pytest.approx(result.total, 0.01) == 25.5
    assert result.breakdown["hp_ratio"] == 0.5
    assert result.breakdown["armour"] == 2.0
    assert result.breakdown["dodge"] == 3.0
    assert result.breakdown["melee"] == 4.0
    assert result.breakdown["ranged"] == 5.0
    assert result.breakdown["speed"] == 6.0
    assert result.breakdown["status_effects"] == 2.0
    assert result.breakdown["level_difference"] == 3.0


def test_evaluate_uses_calculate_score(
    mock_session, mock_user, mock_ai_opponent, caplog
):
    opponent = MagicMock(
        slug="enemy",
        hp_ratio=0.5,
        armour=1,
        dodge=1,
        melee=1,
        ranged=1,
        speed=1,
        level=12,
    )
    opponent.status.get_statuses.return_value = []

    config = MagicMock(
        health_weight=1.0,
        armour_weight=1.0,
        dodge_weight=1.0,
        melee_weight=1.0,
        ranged_weight=1.0,
        speed_weight=1.0,
        status_effects={},
        status_effects_weight=0.0,
        level_difference_threshold=1,
        level_difference_weight=1.0,
    )
    mock_ai_opponent.rules = {"trainer_slug": config}

    evaluator = OpponentEvaluator(
        mock_session, mock_user, [opponent], mock_ai_opponent
    )

    with caplog.at_level("DEBUG"):
        score = evaluator.evaluate(opponent)

    assert score == pytest.approx(7.5, 0.01)
    assert "Evaluation breakdown" in caplog.text
    assert "Final total score" in caplog.text


def test_get_best_target_uses_evaluate(
    mock_session, mock_user, mock_ai_opponent
):
    opponent1 = MagicMock(slug="opp1")
    opponent2 = MagicMock(slug="opp2")
    evaluator = OpponentEvaluator(
        mock_session, mock_user, [opponent1, opponent2], mock_ai_opponent
    )
    evaluator.evaluate = MagicMock(
        side_effect=lambda opp: 1 if opp.slug == "opp1" else 2
    )
    best = evaluator.get_best_target()
    assert best == opponent2
