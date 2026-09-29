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
    "new_category, attr, transition, expected_outcome, expected_reason",
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
    new_category,
    attr,
    transition,
    expected_outcome,
    expected_reason,
):
    """The current status decides how it reacts to the new status's category."""
    current = MagicMock()
    current.slug = "old"
    current.on_positive_status = None
    current.on_negative_status = None
    setattr(current, attr, transition)

    new = MagicMock()
    new.slug = "new"
    new.category = new_category

    result = engine.resolve(current, new)

    assert result.outcome == expected_outcome
    assert result.reason == expected_reason
    assert result.replaced_status == current

def test_current_status_response_is_used_not_the_new_one(engine):
    """A monster with 'focused' loses it when a negative status lands."""
    current = MagicMock()
    current.slug = "focused"
    current.category = CategoryStatus.POSITIVE
    current.on_positive_status = ResponseStatus.REPLACED
    current.on_negative_status = ResponseStatus.REMOVED

    new = MagicMock()
    new.slug = "burn"
    new.category = CategoryStatus.NEGATIVE
    new.on_positive_status = ResponseStatus.REPLACED
    new.on_negative_status = ResponseStatus.REPLACED

    result = engine.resolve(current, new)

    assert result.outcome == ResponseStatus.REMOVED
    assert result.reason == BlockedReason.REMOVED
    assert result.replaced_status == current


@pytest.mark.parametrize(
    "new_category",
    [
        pytest.param(CategoryStatus.POSITIVE, id="incoming_positive"),
        pytest.param(CategoryStatus.NEGATIVE, id="incoming_negative"),
    ],
)
def test_missing_response_is_sticky(engine, new_category):
    """An unset response means the current status remains and blocks the new one."""
    current = MagicMock()
    current.slug = "exhausted"
    current.category = CategoryStatus.NEGATIVE
    current.on_positive_status = None
    current.on_negative_status = None

    new = MagicMock()
    new.slug = "new"
    new.category = new_category

    result = engine.resolve(current, new)

    assert result.outcome == ResponseStatus.BLOCKED
    assert result.reason == BlockedReason.NO_EFFECT
    assert result.replaced_status == current


def test_uncategorised_status_always_lands(engine):
    """Bookkeeping statuses (faint, eliminated) are not blocked by stickiness."""
    current = MagicMock()
    current.slug = "noddingoff"
    current.category = CategoryStatus.NEGATIVE
    current.on_positive_status = None
    current.on_negative_status = None

    new = MagicMock()
    new.slug = "faint"
    new.category = CategoryStatus.NEUTRAL

    result = engine.resolve(current, new)

    assert result.outcome == ResponseStatus.REPLACED
    assert result.reason == BlockedReason.REPLACED
    assert result.replaced_status == current

def test_neutral_category_defaults_to_replaced(engine):
    current = MagicMock()
    current.slug = "old"
    current.on_positive_status = ResponseStatus.REMOVED
    current.on_negative_status = ResponseStatus.REMOVED

    new = MagicMock()
    new.slug = "new"
    new.category = CategoryStatus.NEUTRAL

    result = engine.resolve(current, new)

    assert result.outcome == ResponseStatus.REPLACED
    assert result.reason == BlockedReason.REPLACED
    assert result.replaced_status == current


def test_unknown_outcome_reason(engine):
    current = MagicMock()
    current.slug = "old"
    current.on_positive_status = "unexpected_value"

    new = MagicMock()
    new.slug = "new"
    new.category = CategoryStatus.POSITIVE

    result = engine.resolve(current, new)

    assert result.outcome == "unexpected_value"
    assert result.reason == BlockedReason.NO_EFFECT
    assert result.replaced_status == current
