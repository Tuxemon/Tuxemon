# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.event.eventmiddleware import ButtonFilterMiddleware
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput


@pytest.fixture
def button_filter():
    return ButtonFilterMiddleware()


def test_event_passes_through_if_not_blocked(button_filter):
    event = PlayerInput(button=buttons.UP, value=1, hold_time=0)
    assert button_filter.preprocess(event) is event


def test_event_blocked_if_in_blocklist(button_filter):
    button_filter.block_button(buttons.UP)
    event = PlayerInput(button=buttons.UP, value=1, hold_time=0)
    assert button_filter.preprocess(event) is None


def test_unblock_button_allows_event(button_filter):
    button_filter.block_button(buttons.UP)
    button_filter.unblock_button(buttons.UP)
    event = PlayerInput(button=buttons.UP, value=1, hold_time=0)
    assert button_filter.preprocess(event) is event


def test_initially_blocked_buttons_constructor():
    mw = ButtonFilterMiddleware(initially_blocked_buttons={buttons.DOWN})
    event = PlayerInput(button=buttons.DOWN, value=1, hold_time=0)
    assert mw.preprocess(event) is None


def test_postprocess_returns_event(button_filter):
    event = PlayerInput(button=buttons.LEFT, value=1, hold_time=0)
    assert button_filter.postprocess(event) is event


def test_postprocess_none(button_filter):
    assert button_filter.postprocess(None) is None
