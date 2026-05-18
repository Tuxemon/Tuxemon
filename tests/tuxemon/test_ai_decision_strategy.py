# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.ai.ai import (
    AIConfigLoader,
    AIItems,
    ItemEntry,
    TrainerAIDecisionStrategy,
    WildAIDecisionStrategy,
)


@pytest.fixture
def strategy_base():
    return TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )


@pytest.fixture
def mock_ai():
    ai = MagicMock()
    ai.character.slug = "trainer1"
    ai.character.items = []
    ai.monster.slug = "monster1"
    ai.monster.wild = False
    ai.monster.moves.get_fallback_moves.return_value = []
    return ai


@pytest.fixture
def mock_tracker():
    tracker = MagicMock()
    tracker.get_valid_moves.return_value = [
        (MagicMock(slug="tackle"), MagicMock(slug="enemy"))
    ]
    tracker.evaluate_technique.return_value = 1.0
    return tracker


@pytest.fixture
def mock_evaluator():
    evaluator = MagicMock()
    evaluator.get_best_target.return_value = MagicMock(slug="enemy")
    return evaluator


def test_choose_best_scored_move_picks_highest(strategy_base):
    ai = MagicMock()
    config = MagicMock()

    move1 = (MagicMock(slug="a"), MagicMock(slug="enemy"))
    move2 = (MagicMock(slug="b"), MagicMock(slug="enemy"))

    ai.tracker.evaluate_technique.side_effect = [1.0, 5.0]

    result = strategy_base.choose_best_scored_move(ai, [move1, move2], config)
    assert result == move2


def test_choose_best_scored_move_tie_returns_first(strategy_base):
    ai = MagicMock()
    config = MagicMock()

    move1 = (MagicMock(slug="a"), MagicMock(slug="enemy"))
    move2 = (MagicMock(slug="b"), MagicMock(slug="enemy"))

    ai.tracker.evaluate_technique.side_effect = [5.0, 5.0]

    result = strategy_base.choose_best_scored_move(ai, [move1, move2], config)
    assert result == move1


def test_choose_best_scored_move_negative_scores(strategy_base):
    ai = MagicMock()
    config = MagicMock()

    move1 = (MagicMock(slug="a"), MagicMock(slug="enemy"))
    move2 = (MagicMock(slug="b"), MagicMock(slug="enemy"))

    ai.tracker.evaluate_technique.side_effect = [-10.0, -5.0]

    result = strategy_base.choose_best_scored_move(ai, [move1, move2], config)
    assert result == move2


# TrainerAIDecisionStrategy tests
def test_make_decision_use_potion(mock_ai, mock_evaluator, mock_tracker):
    mock_item = MagicMock(slug="potion")
    mock_ai.character.items = [mock_item]
    mock_ai.character.bag = MagicMock()
    mock_ai.character.bag._items = [mock_item]
    mock_ai.monster.hp_ratio = 0.40

    with patch.object(
        AIConfigLoader,
        "get_ai_items",
        return_value=AIItems(items={"potion": ItemEntry(hp_range=(0.2, 0.8))}),
    ):
        strategy = TrainerAIDecisionStrategy(
            mock_evaluator,
            mock_tracker,
            MagicMock(),
            AIItems(items={"potion": ItemEntry(hp_range=(0.2, 0.8))}),
            MagicMock(),
        )
        strategy.make_decision(mock_ai)

    mock_ai.action_item.assert_called_once_with(mock_item)


def test_make_decision_select_move(mock_ai, mock_evaluator, mock_tracker):
    mock_ai.get_available_moves.return_value = [
        (MagicMock(slug="tackle"), MagicMock(slug="enemy"))
    ]
    mock_tracker.evaluate_technique.return_value = 10.0

    strategy = TrainerAIDecisionStrategy(
        mock_evaluator, mock_tracker, MagicMock(), MagicMock(), MagicMock()
    )
    strategy.make_decision(mock_ai)

    mock_ai.get_available_moves.assert_called_once()
    mock_ai.action_tech.assert_called_once()


def test_select_move_no_valid_actions(mock_ai, mock_evaluator, mock_tracker):
    valid_actions = []
    mock_ai.get_available_moves.return_value = []
    target = MagicMock(slug="enemy")
    mock_fallback = MagicMock(slug="skip")
    mock_ai.monster.moves.get_fallback_moves.return_value = [mock_fallback]

    strategy = TrainerAIDecisionStrategy(
        mock_evaluator, mock_tracker, MagicMock(), MagicMock(), MagicMock()
    )

    technique, chosen_target = strategy.select_move(
        mock_ai, target, valid_actions
    )
    assert technique == mock_fallback
    assert chosen_target == target


def test_handle_monster_config_executes_technique(
    mock_ai, mock_evaluator, mock_tracker
):
    technique = MagicMock(slug="fireball")
    opponent = MagicMock(slug="enemy")
    valid_actions = [(technique, opponent)]
    monster_config = MagicMock()
    monster_config.techniques = [
        MagicMock(technique="fireball", condition=None)
    ]
    strategy = TrainerAIDecisionStrategy(
        mock_evaluator, mock_tracker, MagicMock(), MagicMock(), MagicMock()
    )
    result = strategy.handle_monster_config(
        mock_ai, monster_config, valid_actions
    )
    assert result == (technique, opponent)


def test_need_healing_returns_false_for_unknown_item(
    mock_ai, mock_evaluator, mock_tracker
):
    item = MagicMock(slug="unknown")
    ai_items = MagicMock()
    ai_items.items = {}  # no entry

    strategy = TrainerAIDecisionStrategy(
        mock_evaluator, mock_tracker, MagicMock(), ai_items, MagicMock()
    )
    assert strategy.need_healing(mock_ai, item) is False


def test_check_ai_techs_returns_correct_config(mock_evaluator, mock_tracker):
    ai_techs = MagicMock()
    ai_techs.techniques = {
        "wildslug": "wildconfig",
        "trainer_slug": "trainerconfig",
    }

    wild_monster = MagicMock(slug="wildslug", wild=True)
    trainer_monster = MagicMock(slug="trainer_slug", wild=False)
    trainer_monster.get_owner.return_value = MagicMock(slug="trainer_slug")

    strategy = TrainerAIDecisionStrategy(
        mock_evaluator, mock_tracker, MagicMock(), MagicMock(), ai_techs
    )

    assert strategy.check_ai_techs(wild_monster) == "wildconfig"
    assert strategy.check_ai_techs(trainer_monster) == "trainerconfig"


def test_select_move_uses_fallback_when_no_valid_moves(mock_ai):
    valid_actions = []
    mock_ai.get_available_moves.return_value = []
    fallback = MagicMock(slug="fallback")
    mock_ai.monster.moves.get_fallback_moves.return_value = [fallback]
    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    technique, target = strategy.select_move(
        mock_ai, MagicMock(), valid_actions
    )
    assert technique == fallback


def test_select_move_empty_fallback_raises(mock_ai):
    valid_actions = []
    mock_ai.get_available_moves.return_value = []
    mock_ai.monster.moves.get_fallback_moves.return_value = []
    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )

    with pytest.raises(IndexError):
        strategy.select_move(mock_ai, MagicMock(), valid_actions)


def test_handle_monster_config_skips_unavailable_technique(mock_ai):
    valid_actions = [(MagicMock(slug="tackle"), MagicMock(slug="enemy"))]
    monster_config = MagicMock()
    monster_config.techniques = [
        MagicMock(technique="fireball", condition=None)
    ]

    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    result = strategy.handle_monster_config(
        mock_ai, monster_config, valid_actions
    )
    assert result is None
    mock_ai.action_tech.assert_not_called()


def test_handle_monster_config_skips_when_condition_false(mock_ai):
    technique = MagicMock(slug="fireball")
    opponent = MagicMock(slug="enemy")
    valid_actions = [(technique, opponent)]
    monster_config = MagicMock()
    monster_config.techniques = [
        MagicMock(technique="fireball", condition="hp_below_50")
    ]

    with patch(
        "tuxemon.ai.decision_strategy.check_tech_conditions",
        return_value=False,
    ):
        strategy = TrainerAIDecisionStrategy(
            MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
        )
        result = strategy.handle_monster_config(
            mock_ai, monster_config, valid_actions
        )
        assert result is None

    mock_ai.action_tech.assert_not_called()


def test_handle_monster_config_executes_first_valid(mock_ai):
    t1 = MagicMock(slug="fireball")
    t2 = MagicMock(slug="icebeam")
    opp = MagicMock(slug="enemy")
    valid_actions = [(t1, opp), (t2, opp)]
    monster_config = MagicMock()
    monster_config.techniques = [
        MagicMock(technique="fireball", condition=None),
        MagicMock(technique="icebeam", condition=None),
    ]
    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    result = strategy.handle_monster_config(
        mock_ai, monster_config, valid_actions
    )
    assert result == (t1, opp)


def test_need_healing_item_condition_false():
    ai = MagicMock()
    ai.monster.hp_ratio = 0.9
    item = MagicMock(slug="potion")

    ai_items = AIItems(items={"potion": ItemEntry(hp_range=(0.0, 0.2))})

    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), ai_items, MagicMock()
    )

    assert strategy.need_healing(ai, item) is False


def test_make_decision_uses_first_valid_item(mock_ai):
    item1 = MagicMock(slug="potion")
    item2 = MagicMock(slug="superpotion")

    mock_ai.character.items = [item1, item2]
    mock_ai.monster.hp_ratio = 0.3

    ai_items = AIItems(
        items={
            "potion": ItemEntry(hp_range=(0.0, 0.5)),
            "superpotion": ItemEntry(hp_range=(0.0, 0.5)),
        }
    )

    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), ai_items, MagicMock()
    )

    strategy.make_decision(mock_ai)
    mock_ai.action_item.assert_called_once_with(item1)


def test_default_decision_calls_select_and_action(mock_ai):
    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    mock_ai.evaluate_best_opponent.return_value = MagicMock(slug="enemy")
    valid_actions = [(MagicMock(), MagicMock())]

    with patch.object(
        strategy, "select_move", return_value=(MagicMock(), MagicMock())
    ) as sm:
        strategy.default_decision(mock_ai, valid_actions)

    sm.assert_called_once()
    mock_ai.action_tech.assert_called_once()


def test_check_ai_techs_no_owner_config():
    ai_techs = MagicMock()
    ai_techs.techniques = {}

    monster = MagicMock(slug="x", wild=False)
    monster.get_owner.return_value = MagicMock(slug="owner")

    strategy = TrainerAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), ai_techs
    )

    assert strategy.check_ai_techs(monster) is None


# WildAIDecisionStrategy tests
def test_wild_ai_make_decision(mock_ai, mock_evaluator, mock_tracker):
    mock_ai.get_available_moves.return_value = [
        (MagicMock(slug="scratch"), MagicMock(slug="enemy"))
    ]
    mock_ai.tracker.evaluate_technique.return_value = 5.0
    mock_tracker.evaluate_technique.return_value = 5.0
    mock_evaluator.get_best_target.return_value = MagicMock(slug="enemy")

    mock_trainers = MagicMock()
    mock_items = MagicMock()
    mock_techs = MagicMock()

    strategy = WildAIDecisionStrategy(
        mock_evaluator,
        mock_tracker,
        mock_trainers,
        mock_items,
        mock_techs,
    )

    strategy.make_decision(mock_ai)
    mock_ai.action_tech.assert_called_once()


def test_wild_ai_random_when_no_config(mock_ai):
    mock_ai.get_available_moves.return_value = [
        (MagicMock(slug="scratch"), MagicMock(slug="enemy"))
    ]

    mock_techs = MagicMock()
    mock_techs.techniques = {}

    strategy = WildAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), mock_techs
    )

    strategy.make_decision(mock_ai)
    mock_ai.action_tech.assert_called_once()


def test_wild_ai_uses_best_scored_move(mock_ai):
    move1 = (MagicMock(slug="a"), MagicMock(slug="enemy"))
    move2 = (MagicMock(slug="b"), MagicMock(slug="enemy"))

    mock_ai.get_available_moves.return_value = [move1, move2]
    mock_ai.tracker.evaluate_technique.side_effect = [1.0, 10.0]

    ai_techs = MagicMock()
    ai_techs.techniques = {"monster1": MagicMock()}

    mock_ai.monster.wild = True

    strategy = WildAIDecisionStrategy(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(), ai_techs
    )

    strategy.make_decision(mock_ai)
    mock_ai.action_tech.assert_called_once_with(*move2)
