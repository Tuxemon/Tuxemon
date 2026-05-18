# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import BlockedReason, CategoryStatus, ResponseStatus
from tuxemon.status.transition_engine import TransitionEngine


@pytest.fixture
def engine():
    return TransitionEngine()


@pytest.fixture
def status():
    s = MagicMock()
    s.slug = "test"
    s.category = None
    s.on_positive_status = None
    s.on_negative_status = None
    return s


def test_no_current_status(engine, status):
    result = engine.resolve(None, status)
    assert result.outcome == ResponseStatus.REPLACED
    assert result.reason == BlockedReason.REPLACED
    assert result.replaced_status is None


def test_stacking(engine):
    current = MagicMock(slug="burn")
    new = MagicMock(slug="burn")

    result = engine.resolve(current, new)

    assert result.outcome == ResponseStatus.STACKED
    assert result.reason == BlockedReason.ALREADY_PRESENT
    assert result.replaced_status == current


@pytest.mark.parametrize(
    "category, attr, transition, expected_outcome, expected_reason",
    [
        pytest.param(
            CategoryStatus.POSITIVE,
            "on_positive_status",
            ResponseStatus.REPLACED,
            ResponseStatus.REPLACED,
            BlockedReason.REPLACED,
            id="pos_replace",
        ),
        pytest.param(
            CategoryStatus.POSITIVE,
            "on_positive_status",
            ResponseStatus.REMOVED,
            ResponseStatus.REMOVED,
            BlockedReason.REMOVED,
            id="pos_remove",
        ),
        pytest.param(
            CategoryStatus.NEGATIVE,
            "on_negative_status",
            ResponseStatus.REPLACED,
            ResponseStatus.REPLACED,
            BlockedReason.REPLACED,
            id="neg_replace",
        ),
        pytest.param(
            CategoryStatus.NEGATIVE,
            "on_negative_status",
            ResponseStatus.REMOVED,
            ResponseStatus.REMOVED,
            BlockedReason.REMOVED,
            id="neg_remove",
        ),
    ],
)
def test_category_transitions(
    engine,
    category,
    attr,
    transition,
    expected_outcome,
    expected_reason,
):
    current = MagicMock()
    current.slug = "old"
    current.category = category

    new = MagicMock()
    setattr(new, attr, transition)

    result = engine.resolve(current, new)

    assert result.outcome == expected_outcome
    assert result.reason == expected_reason
    assert result.replaced_status == current


def test_neutral_category_defaults_to_replaced(engine):
    current = MagicMock()
    current.slug = "old"
    current.category = CategoryStatus.NEUTRAL

    new = MagicMock()
    new.on_positive_status = None
    new.on_negative_status = None

    result = engine.resolve(current, new)

    assert result.outcome == ResponseStatus.REPLACED
    assert result.reason == BlockedReason.REPLACED
    assert result.replaced_status == current


def test_unknown_outcome_reason(engine):
    current = MagicMock()
    current.slug = "old"
    current.category = CategoryStatus.POSITIVE

    new = MagicMock()
    new.on_positive_status = "unexpected_value"

    result = engine.resolve(current, new)

    assert result.outcome == "unexpected_value"
    assert result.reason == BlockedReason.NO_EFFECT
    assert result.replaced_status == current
