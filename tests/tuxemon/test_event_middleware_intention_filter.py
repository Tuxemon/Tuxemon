# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.event.eventmiddleware import IntentionFilterMiddleware
from tuxemon.platform.const import intentions
from tuxemon.platform.events import PlayerInput


@pytest.fixture
def intention_filter():
    return IntentionFilterMiddleware()


def test_global_block_consumes_event(intention_filter):
    event = PlayerInput(button=intentions.UP, value=1, hold_time=0)
    assert intention_filter.preprocess(event) is None


def test_allow_specific_action(intention_filter):
    intention_filter.update_allowed_actions({intentions.UP})
    event = PlayerInput(button=intentions.UP, value=1, hold_time=0)
    assert intention_filter.preprocess(event) is event


def test_block_unlisted_action(intention_filter):
    intention_filter.update_allowed_actions({intentions.UP})
    event = PlayerInput(button=intentions.DOWN, value=1, hold_time=0)
    assert intention_filter.preprocess(event) is None


def test_open_gate_allows_everything(intention_filter):
    intention_filter.update_allowed_actions(
        IntentionFilterMiddleware.OPEN_GATE
    )
    event1 = PlayerInput(button=intentions.UP, value=1, hold_time=0)
    event2 = PlayerInput(button=intentions.DOWN, value=1, hold_time=0)
    assert intention_filter.preprocess(event1) is event1
    assert intention_filter.preprocess(event2) is event2


def test_postprocess_returns_event(intention_filter):
    event = PlayerInput(button=intentions.LEFT, value=1, hold_time=0)
    assert intention_filter.postprocess(event) is event


def test_postprocess_none(intention_filter):
    assert intention_filter.postprocess(None) is None
