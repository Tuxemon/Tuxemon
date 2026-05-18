# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.core.asset import init_assets
from tuxemon.db import CategoryStatus, EffectPhase, ResponseStatus
from tuxemon.monster.monster import Monster
from tuxemon.monster.status import MonsterStatusHandler


@pytest.fixture
def session():
    init_assets()
    return MagicMock()


@pytest.fixture
def monster():
    m = MagicMock(spec=Monster)
    m.name = "Rockitten"
    return m


@pytest.fixture
def basic_handler():
    return MonsterStatusHandler()


@pytest.fixture
def status(monster):
    s = MagicMock(slug="test")
    s.host = monster
    return s


def test_init(basic_handler):
    assert basic_handler.status == []


def test_init_with_status(status):
    handler = MonsterStatusHandler([status])
    assert handler.status == [status]


def test_apply_status(session, monster, status):
    monster.held_item = MagicMock()
    monster.held_item.is_immune.return_value = False
    handler = MonsterStatusHandler()
    handler.apply_status(session, status)
    assert handler.status == [status]


def test_clear_status(session, status):
    handler = MonsterStatusHandler([status])
    handler.clear_status(session)
    assert handler.status == []


def test_get_statuses(status):
    handler = MonsterStatusHandler([status])
    assert handler.get_statuses() == [status]


def test_status_exists(status):
    handler = MonsterStatusHandler([status])
    assert handler.status_exists()


def test_status_exists_not(basic_handler):
    assert not basic_handler.status_exists()


def test_remove_bonded_statuses(session):
    s1 = MagicMock(bond=True)
    s2 = MagicMock(bond=False)
    handler = MonsterStatusHandler([s1, s2])
    handler.remove_bonded_statuses(session)
    assert handler.status == [s2]


def test_immunity_blocks_status(session, monster, status):
    monster.held_item = MagicMock()
    monster.held_item.is_immune.return_value = True
    handler = MonsterStatusHandler()
    result = handler.apply_status(session, status)
    assert not result.applied
    assert result.blocked_reason.name == "IMMUNE_BY_ITEM"
    assert handler.status == []


def test_stack_called_on_duplicate_status(session, monster):
    s1 = MagicMock(slug="burn")
    s1.host = monster
    s1.stack = MagicMock()
    s2 = MagicMock(slug="burn")
    s2.host = monster
    monster.held_item = MagicMock()
    monster.held_item.is_immune.return_value = False
    handler = MonsterStatusHandler([s1])
    handler.apply_status(session, s2)
    s1.stack.assert_called_once()


def test_on_start_called(session, monster):
    s = MagicMock(slug="burn")
    s.host = monster
    monster.held_item = MagicMock()
    monster.held_item.is_immune.return_value = False
    handler = MonsterStatusHandler()
    handler.apply_status(session, s)
    s.use.assert_called_with(session, EffectPhase.ON_START)


def test_on_end_called(session, monster):
    s1 = MagicMock(slug="burn")
    s1.host = monster
    s2 = MagicMock(slug="freeze")
    s2.host = monster
    monster.held_item = MagicMock()
    monster.held_item.is_immune.return_value = False
    handler = MonsterStatusHandler([s1])
    handler.apply_status(session, s2)
    s1.use.assert_any_call(session, EffectPhase.ON_END)


def test_tick_statuses_on_steps(monster, session):
    s = MagicMock()
    s.tick_steps.return_value = "result"
    handler = MonsterStatusHandler([s])
    results = handler.tick_statuses_on_steps(session, 5)
    assert results == ["result"]
    s.tick_steps.assert_called_once()


def test_check_and_clear_use_expiry(monster, session):
    s = MagicMock()
    s.host = monster
    s.is_use_expired.return_value = True
    handler = MonsterStatusHandler([s])
    cleared = handler.check_and_clear_use_expiry(session)
    assert cleared
    assert handler.status == []


@patch("tuxemon.status.status.StatusModel.lookup")
def test_apply_item_statuses(mock_lookup, monster):
    mock_lookup.return_value = MagicMock(
        slug="enraged",
        sort=None,
        gain_cond=None,
        use_success=None,
        use_failure=None,
        icon="",
        modifiers=[],
        behaviors=MagicMock(),
        step_interval=0,
        step_effect_value=0,
        step_effect_type=0,
        stat_modifiers={},
        duration=0,
        bond=False,
        category=None,
        on_negative_status=None,
        on_positive_status=None,
        on_tech_use=None,
        on_item_use=None,
        cond_id=0,
        effects=[],
        conditions=[],
        visuals=MagicMock(),
        sound=MagicMock(),
    )
    item = MagicMock()
    item.granted_statuses = ["enraged"]
    handler = MonsterStatusHandler()
    handler.apply_item_statuses(monster, item)
    assert len(handler.status) == 1
    assert handler.status[0].slug == "enraged"


def test_remove_item_statuses(monster):
    s1 = MagicMock(slug="enraged")
    s2 = MagicMock(slug="burn")
    item = MagicMock()
    item.granted_statuses = ["enraged"]
    handler = MonsterStatusHandler([s1, s2])
    handler.remove_item_statuses(item)
    assert handler.status == [s2]


@patch("tuxemon.status.status.StatusModel.lookup")
def test_decode_status(mock_lookup, monster):
    mock_lookup.return_value = MagicMock(
        slug="burn",
        sort=None,
        gain_cond=None,
        use_success=None,
        use_failure=None,
        icon="",
        modifiers=[],
        behaviors=MagicMock(),
        step_interval=0,
        step_effect_value=0,
        step_effect_type=0,
        stat_modifiers={},
        duration=0,
        bond=False,
        category=None,
        on_negative_status=None,
        on_positive_status=None,
        on_tech_use=None,
        on_item_use=None,
        cond_id=0,
        effects=[],
        conditions=[],
        visuals=MagicMock(),
        sound=MagicMock(),
    )
    json_data = {
        "status": [
            {"slug": "burn", "steps": 0},
            {"slug": "freeze", "steps": 0},
        ]
    }
    handler = MonsterStatusHandler()
    handler.decode_status(json_data, monster)
    assert len(handler.status) == 2


@pytest.mark.parametrize(
    "slug, expected",
    [
        pytest.param("test", True, id="status_present"),
        pytest.param("other", False, id="status_absent"),
    ],
)
def test_has_status_param(monster, slug, expected):
    s = MagicMock(slug="test")
    s.host = monster

    handler = MonsterStatusHandler([s])

    assert handler.has_status(slug) == expected


@pytest.mark.parametrize(
    "current_category, transition, expect_applied, expect_empty",
    [
        pytest.param(
            CategoryStatus.POSITIVE,
            ResponseStatus.REPLACED,
            True,
            False,
            id="positive_replaced",
        ),
        pytest.param(
            CategoryStatus.POSITIVE,
            ResponseStatus.REMOVED,
            False,
            True,
            id="positive_removed",
        ),
        pytest.param(
            CategoryStatus.NEGATIVE,
            ResponseStatus.REPLACED,
            True,
            False,
            id="negative_replaced",
        ),
        pytest.param(
            CategoryStatus.NEGATIVE,
            ResponseStatus.REMOVED,
            False,
            True,
            id="negative_removed",
        ),
        pytest.param(
            None,
            ResponseStatus.REPLACED,
            True,
            False,
            id="neutral_defaults_replaced",
        ),
    ],
)
def test_apply_status_transitions(
    session,
    monster,
    current_category,
    transition,
    expect_applied,
    expect_empty,
):
    status1 = MagicMock(category=current_category)
    status1.host = monster

    status2 = MagicMock()
    status2.host = monster

    if current_category == CategoryStatus.POSITIVE:
        status2.on_positive_status = transition
    elif current_category == CategoryStatus.NEGATIVE:
        status2.on_negative_status = transition

    monster.held_item = MagicMock()
    monster.held_item.is_immune.return_value = False

    handler = MonsterStatusHandler([status1])
    result = handler.apply_status(session, status2)

    assert result.applied == expect_applied
    assert (handler.status == []) == expect_empty
