# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from tuxemon.db import EvolutionStage, LearningMethod
from tuxemon.monster.moves import MonsterMovesHandler


class DummyMonster:
    def __init__(self, level=5, stage="basic", max_moves=4):
        self.level = level
        self.stage = stage
        self.max_moves = max_moves
        self.slug = "dummy"
        self.iid = UUID("123e4567-e89b-12d3-a456-426655440000")


@pytest.fixture
def handler():
    return MonsterMovesHandler()


@pytest.fixture
def technique():
    tech = MagicMock()
    tech.slug = "techniqueX"
    tech.instance_id = UUID("00000000-0000-0000-0000-000000000001")
    return tech


@pytest.fixture
def monster():
    return DummyMonster()


def test_init(handler):
    assert handler.moves == []
    assert handler.moveset == []

    moves = [MagicMock()]
    moveset = [MagicMock()]
    h = MonsterMovesHandler(moves, moveset)

    assert h.moves == moves
    assert h.moveset == list(moveset)


def test_set_moveset(handler):
    moveset = [MagicMock()]
    handler.set_moveset(moveset)
    assert handler.moveset == list(moveset)


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("learn", id="learn"),
        pytest.param("forget", id="forget"),
    ],
)
@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_learn_and_forget(_mock, handler, monster, technique, method):
    handler.learn(monster, technique)
    if method == "forget":
        handler.forget(technique)
        assert technique not in handler.moves
    else:
        assert technique in handler.moves


@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_replace_move(_mock, handler, monster):
    t1 = MagicMock()
    t2 = MagicMock()
    handler.learn(monster, t1)
    handler.replace_move(0, t2)
    assert handler.moves[0] is t2


def test_set_moves(handler, monster):
    moveset = [
        MagicMock(
            level_learned=1,
            technique="technique1",
            evolution_stage_learned=None,
            learning_method=LearningMethod.LEVEL_UP,
        ),
        MagicMock(
            level_learned=2,
            technique="technique2",
            evolution_stage_learned=None,
            learning_method=LearningMethod.LEVEL_UP,
        ),
    ]

    with (
        patch("tuxemon.technique.technique.Technique.create") as mock_create,
        patch.object(
            MonsterMovesHandler,
            "is_eligible",
            side_effect=lambda m, slug, method=None: (
                slug in {"technique1", "technique2"}
            ),
        ),
    ):
        mock_create.side_effect = lambda slug: MagicMock(slug=slug)
        handler.set_moveset(moveset)
        handler.set_moves(monster, 2)

        assert {m.slug for m in handler.moves} == {"technique1", "technique2"}


def test_update_moves(handler, monster):
    moveset = [
        MagicMock(
            level_learned=1,
            technique="technique1",
            evolution_stage_learned=None,
            learning_method=LearningMethod.LEVEL_UP,
        ),
        MagicMock(
            level_learned=2,
            technique="technique2",
            evolution_stage_learned=None,
            learning_method=LearningMethod.LEVEL_UP,
        ),
        MagicMock(
            level_learned=3,
            technique="technique3",
            evolution_stage_learned=None,
            learning_method=LearningMethod.LEVEL_UP,
        ),
    ]

    with (
        patch("tuxemon.technique.technique.Technique.create") as mock_create,
        patch.object(MonsterMovesHandler, "is_eligible", return_value=True),
    ):
        mock_create.side_effect = lambda slug: MagicMock(slug=slug)

        handler.set_moveset(moveset)
        handler.set_moves(monster, 2)

        monster.level = 3
        new = handler.update_moves(monster, 1)

        assert [t.slug for t in new] == ["technique3"]


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("recharge_moves", id="recharge_moves"),
        pytest.param("full_recharge_moves", id="full_recharge_moves"),
        pytest.param("reset_current_stats", id="reset_current_stats"),
    ],
)
@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_recharge_and_stats(_mock, handler, monster, technique, method):
    handler.learn(monster, technique)
    getattr(handler, method)()


@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_find_tech_by_id(_mock, handler, monster, technique):
    handler.learn(monster, technique)
    found = handler.find_tech_by_id(technique.instance_id)
    assert found is technique


@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_has_moves(_mock, handler, monster, technique):
    assert not handler.has_moves()
    handler.learn(monster, technique)
    assert handler.has_moves()


@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_has_move(_mock, handler, monster, technique):
    handler.learn(monster, technique)
    assert handler.has_move(technique.slug)


@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_get_moves(_mock, handler, monster, technique):
    handler.learn(monster, technique)
    assert technique in handler.get_moves()


@pytest.mark.parametrize(
    "can_be_forgotten, expected",
    [
        pytest.param(True, True, id="can_forget"),
        pytest.param(False, False, id="cannot_forget"),
    ],
)
def test_can_forget(handler, can_be_forgotten, expected):
    entry = MagicMock(
        technique="fireball" if expected else "icewall",
        can_be_forgotten=can_be_forgotten,
    )
    handler.set_moveset([entry])
    tech = MagicMock(slug=entry.technique)
    assert handler.can_forget(tech) is expected


@patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
def test_remove_forced(_mock, handler, monster, technique):
    technique.slug = "shockwave"
    handler.learn(monster, technique)
    removed = handler.remove_forced(technique)
    assert removed
    assert technique not in handler.moves


def test_is_eligible_stage_mismatch(handler, monster):
    move = MagicMock(
        technique="wave",
        level_learned=3,
        evolution_stage_learned=EvolutionStage.STAGE2,
        learning_method=LearningMethod.LEVEL_UP,
    )

    handler.set_moveset([move])
    monster.level = 4
    monster.stage = EvolutionStage.BASIC

    assert not handler.is_eligible(
        monster, "wave", method=LearningMethod.LEVEL_UP
    )


def test_is_eligible_stage_match(handler, monster):
    move = MagicMock(
        technique="zap",
        level_learned=2,
        evolution_stage_learned=EvolutionStage.BASIC,
        learning_method=LearningMethod.LEVEL_UP,
    )

    handler.set_moveset([move])
    monster.level = 3
    monster.stage = EvolutionStage.BASIC

    assert handler.is_eligible(monster, "zap", method=LearningMethod.LEVEL_UP)


def test_apply_item_techniques_adds_moves():
    handler = MonsterMovesHandler()
    monster = DummyMonster(max_moves=2)
    item = MagicMock()
    item.granted_techniques = ["fireball", "icebeam"]
    with patch("tuxemon.technique.technique.Technique.create") as mock_create:
        mock_create.side_effect = lambda slug: MagicMock(slug=slug)

        handler.apply_item_techniques(monster, item)
    assert {m.slug for m in handler.moves} == {"fireball", "icebeam"}
    assert monster.max_moves == 4


def test_remove_item_techniques_removes_moves_and_reduces_capacity():
    handler = MonsterMovesHandler()
    monster = DummyMonster(max_moves=4)
    handler.moves = [
        MagicMock(slug="fireball"),
        MagicMock(slug="icebeam"),
        MagicMock(slug="tackle"),
    ]
    item = MagicMock()
    item.granted_techniques = ["fireball", "icebeam"]
    handler.remove_item_techniques(monster, item)
    assert {m.slug for m in handler.moves} == {"tackle"}
    assert monster.max_moves == 2


def test_apply_item_techniques_does_not_duplicate_moves():
    handler = MonsterMovesHandler()
    monster = DummyMonster(max_moves=3)
    handler.moves = [MagicMock(slug="fireball")]
    item = MagicMock()
    item.granted_techniques = ["fireball", "icebeam"]
    with patch("tuxemon.technique.technique.Technique.create") as mock_create:
        mock_create.side_effect = lambda slug: MagicMock(slug=slug)

        handler.apply_item_techniques(monster, item)

    assert {m.slug for m in handler.moves} == {"fireball", "icebeam"}
    assert monster.max_moves == 4


def test_remove_item_techniques_never_negative_capacity():
    handler = MonsterMovesHandler()
    monster = DummyMonster(max_moves=1)
    handler.moves = [MagicMock(slug="fireball")]
    item = MagicMock()
    item.granted_techniques = ["fireball"]
    handler.remove_item_techniques(monster, item)
    assert monster.max_moves == 0
