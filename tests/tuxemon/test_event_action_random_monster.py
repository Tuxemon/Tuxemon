# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import MonsterModel
from tuxemon.event.actions.random_monster import RandomMonsterAction
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventbehavior import BehaviorManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.event.running import ConditionEvaluator
from tuxemon.session import local_session


def make_mock_monster(
    slug,
    *,
    txmn_id=1,
    randomly=True,
    evolves=False,
    underleveled=False,
):
    m = MagicMock()
    m.slug = slug
    m.txmn_id = txmn_id
    m.randomly = randomly
    m.can_evolve_at_level.return_value = evolves
    m.is_underleveled_for_form.return_value = underleveled
    return m


@pytest.fixture
def engine():
    action = ActionManager()
    evaluator = ConditionEvaluator(MagicMock(), MagicMock())
    behavior = BehaviorManager()
    engine = EventEngine(local_session, action, evaluator, behavior)

    engine.execute_action = MagicMock()
    local_session.set_client(MagicMock(event_engine=engine))
    return engine


@pytest.fixture
def set_monster_cache():
    def _set(data):
        MonsterModel._lookup_cache.clear()
        MonsterModel._lookup_cache.update(data)

    yield _set
    MonsterModel._lookup_cache.clear()


def test_random_monster_basic(engine, set_monster_cache):
    set_monster_cache(
        {
            "a": make_mock_monster("a"),
            "b": make_mock_monster("b"),
        }
    )

    action = RandomMonsterAction(monster_level=5)
    action.start(local_session)

    engine.execute_action.assert_called_once()
    slug = engine.execute_action.call_args[0][1][0]
    assert slug in {"a", "b"}


def test_excludes_monsters_that_would_evolve(engine, set_monster_cache):
    set_monster_cache(
        {
            "evo": make_mock_monster("evo", evolves=True),
            "ok": make_mock_monster("ok"),
        }
    )

    action = RandomMonsterAction(monster_level=5)
    action.start(local_session)

    slug = engine.execute_action.call_args[0][1][0]
    assert slug == "ok"


def test_excludes_underleveled_forms(engine, set_monster_cache):
    set_monster_cache(
        {
            "bad": make_mock_monster("bad", underleveled=True),
            "ok": make_mock_monster("ok"),
        }
    )

    action = RandomMonsterAction(monster_level=5)
    action.start(local_session)

    slug = engine.execute_action.call_args[0][1][0]
    assert slug == "ok"


def test_excludes_non_random_monsters(engine, set_monster_cache):
    set_monster_cache(
        {
            "bad": make_mock_monster("bad", randomly=False),
            "ok": make_mock_monster("ok"),
        }
    )

    action = RandomMonsterAction(monster_level=5)
    action.start(local_session)

    slug = engine.execute_action.call_args[0][1][0]
    assert slug == "ok"


def test_no_valid_monsters_logs_error(engine, set_monster_cache, caplog):
    set_monster_cache(
        {
            "bad": make_mock_monster("bad", randomly=False),
        }
    )

    action = RandomMonsterAction(monster_level=5)
    action.start(local_session)

    assert "No valid monsters" in caplog.text
    engine.execute_action.assert_not_called()
