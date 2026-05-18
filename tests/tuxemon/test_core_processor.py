# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, Mock

import pytest

from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import (
    CoreEffect,
    ItemEffectResult,
    StatusEffectResult,
    TechEffectResult,
)
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.technique.technique import Technique


@pytest.fixture
def session():
    return Mock(spec=Session)


@pytest.fixture
def user():
    return Mock()


@pytest.fixture
def target():
    return Mock()


@pytest.fixture
def technique():
    t = Mock()
    t.name = "Fireball"
    return t


# EffectProcessor tests
def test_process_tech(session, technique, user, target):
    tech_effect = Mock(spec=CoreEffect)
    tech_effect.apply_tech_target.return_value = TechEffectResult(
        name="Fireball",
        success=True,
        damage=15,
        element_multiplier=1.5,
        should_tackle=False,
        extras=["Burn"],
    )
    processor = EffectProcessor([tech_effect])

    result = processor.process_tech(session, technique, user, target)
    assert result.success
    assert result.damage == 15
    assert result.element_multiplier == 1.5
    assert result.extras == ["Burn"]


def test_process_tech_failure(session, technique, user, target):
    tech_effect = Mock(spec=CoreEffect)
    tech_effect.apply_tech_target.return_value = TechEffectResult(
        name="Fireball",
        success=False,
        damage=0,
        element_multiplier=1.0,
        should_tackle=False,
        extras=[],
    )
    processor = EffectProcessor([tech_effect])

    result = processor.process_tech(session, technique, user, target)
    assert not result.success


def test_update_calls_effects(session):
    tech_effect = Mock(spec=CoreEffect)
    processor = EffectProcessor([tech_effect])
    processor.update(session, dt=0.1)
    tech_effect.update.assert_called_once_with(session, 0.1)


def test_process_item(session, target):
    item = Mock()
    item.name = "Potion"
    item_effect = Mock(spec=CoreEffect)
    item_effect.apply_item_target.return_value = ItemEffectResult(
        name="Potion", success=True, num_shakes=3, extras=["Healing Boost"]
    )
    processor = EffectProcessor([item_effect])

    result = processor.process_item(session, item, target)
    assert result.success
    assert result.num_shakes == 3
    assert result.extras == ["Healing Boost"]


def test_process_item_failure(session, target):
    item = Mock()
    item.name = "Potion"
    item_effect = Mock(spec=CoreEffect)
    item_effect.apply_item_target.return_value = ItemEffectResult(
        name="Potion", success=False, num_shakes=0, extras=[]
    )
    processor = EffectProcessor([item_effect])

    result = processor.process_item(session, item, target)
    assert not result.success


def test_update_calls_item_effect(session):
    item_effect = Mock(spec=CoreEffect)
    processor = EffectProcessor([item_effect])
    processor.update(session, dt=0.2)
    item_effect.update.assert_called_once_with(session, 0.2)


def test_process_status(session):
    status = Mock()
    status.name = "Poison"
    status_effect = Mock(spec=CoreEffect)
    status_effect.apply_status.return_value = StatusEffectResult(
        name="Poison",
        success=True,
        statuses=["Poisoned"],
        techniques=["Weaken"],
        extras=["Extended Duration"],
    )
    processor = EffectProcessor([status_effect])

    result = processor.process_status(session, status)
    assert result.success
    assert result.statuses == ["Poisoned"]
    assert result.techniques == ["Weaken"]
    assert result.extras == ["Extended Duration"]


def test_update_calls_status_effect(session):
    status_effect = Mock(spec=CoreEffect)
    processor = EffectProcessor([status_effect])
    processor.update(session, dt=0.3)
    status_effect.update.assert_called_once_with(session, 0.3)


# ConditionProcessor tests
@pytest.fixture
def core_condition():
    return MagicMock(spec=CoreCondition)


@pytest.fixture
def target_monster():
    return MagicMock(spec=Monster)


def test_no_conditions(session, target_monster):
    processor = ConditionProcessor([])
    assert processor.validate_monster(session, target_monster).passed


def test_no_target(session, core_condition):
    processor = ConditionProcessor([core_condition])
    assert not processor.validate_monster(session, None).passed


@pytest.mark.parametrize(
    "is_expected, test_result, expected",
    [
        pytest.param(True, True, True, id="expected_true_pass"),
        pytest.param(True, False, False, id="expected_true_fail"),
        pytest.param(False, False, True, id="expected_false_pass"),
        pytest.param(False, True, False, id="expected_false_fail"),
    ],
)
def test_condition_variants(
    session, core_condition, target_monster, is_expected, test_result, expected
):
    core_condition.is_expected = is_expected
    core_condition.test_with_monster.return_value = test_result
    processor = ConditionProcessor([core_condition])
    assert (
        processor.validate_monster(session, target_monster).passed == expected
    )


def test_invalid_condition_type(session, target_monster):
    invalid_condition = MagicMock()
    processor = ConditionProcessor([invalid_condition])
    assert not processor.validate_monster(session, target_monster).passed


def test_multiple_conditions_all_pass(session, core_condition, target_monster):
    core_condition.is_expected = True
    core_condition.test_with_monster.return_value = True
    another = MagicMock(spec=CoreCondition)
    another.is_expected = True
    another.test_with_monster.return_value = True
    processor = ConditionProcessor([core_condition, another])
    assert processor.validate_monster(session, target_monster).passed


def test_multiple_conditions_one_fails(
    session, core_condition, target_monster
):
    core_condition.is_expected = True
    core_condition.test_with_monster.return_value = True
    another = MagicMock(spec=CoreCondition)
    another.is_expected = True
    another.test_with_monster.return_value = False
    processor = ConditionProcessor([core_condition, another])
    assert not processor.validate_monster(session, target_monster).passed


def test_method_invocation_count(session, core_condition, target_monster):
    core_condition.is_expected = True
    core_condition.test_with_monster.return_value = True
    processor = ConditionProcessor([core_condition])
    processor.validate_monster(session, target_monster)
    core_condition.test_with_monster.assert_called_once_with(
        session, target_monster
    )


def test_empty_conditions_with_none_target(session):
    processor = ConditionProcessor([])
    assert processor.validate_monster(session, None).passed


def test_dispatch_to_technique_method(session):
    cond = MagicMock(spec=CoreCondition)
    cond.is_expected = True
    cond.test_with_tech.return_value = True
    target = MagicMock(spec=Technique)
    processor = ConditionProcessor([cond])
    assert processor.validate_tech(session, target)
    cond.test_with_tech.assert_called_once_with(session, target)


def test_monster_overrides_technique_method(session):
    cond = MagicMock(spec=CoreCondition)
    cond.is_expected = True
    cond.test_with_monster.return_value = True
    target = MagicMock(spec=Monster)
    processor = ConditionProcessor([cond])
    assert processor.validate_monster(session, target).passed
    cond.test_with_monster.assert_called_once()
