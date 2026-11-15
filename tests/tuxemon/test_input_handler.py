# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Generator
from typing import Any

import pytest

from tuxemon.platform.events import (
    EventQueueHandler,
    InputHandler,
    PlayerInput,
)


class DummyInputHandler(InputHandler[Any]):
    def process_event(self, input_event: Any) -> None:
        pass


class DummyEventQueueHandler(EventQueueHandler):
    def process_events(self) -> Generator[PlayerInput, None, None]:
        for player_inputs in self._inputs.values():
            for input_handler in player_inputs.values():
                yield from input_handler.get_events()


@pytest.fixture
def handler():
    return DummyInputHandler(event_map={1: 1})


def test_press_sets_value_and_hold_time(handler):
    handler.press(1)
    inp = handler.buttons[1]
    assert inp.value == 1
    assert inp.hold_time == 1
    assert not inp.triggered


def test_release_sets_value_and_triggered(handler):
    handler.press(1)
    handler.release(1)
    inp = handler.buttons[1]
    assert inp.value == 0
    assert inp.hold_time == 0
    assert inp.triggered


def test_virtual_stop_events_yields_released_inputs(handler):
    handler.press(1)
    events = list(handler.virtual_stop_events())
    assert len(events) == 1
    assert events[0].button == 1
    assert events[0].value == 0


def test_get_events_yields_copy_and_updates_state(handler):
    handler.press(1)
    events = list(handler.get_events())
    assert events[0].hold_time == 1
    assert events[0].pressed


def test_get_events_after_release(handler):
    handler.press(1)
    handler.get_events()
    handler.release(1)
    events = list(handler.get_events())
    assert events[0].triggered
    assert events[0].value == 0


def test_press_with_custom_value(handler):
    handler.press(1, value=0.5)
    inp = handler.buttons[1]
    assert inp.value == 0.5
    assert inp.hold_time == 1


def test_release_without_press(handler):
    handler.release(1)
    inp = handler.buttons[1]
    assert inp.value == 0
    assert inp.hold_time == 0
    assert inp.triggered


def test_get_events_with_no_active_inputs(handler):
    assert list(handler.get_events()) == []


def test_virtual_stop_events_with_no_held_buttons(handler):
    assert list(handler.virtual_stop_events()) == []


def test_press_does_not_reset_hold_time(handler):
    handler.press(1)
    list(handler.get_events())
    list(handler.get_events())
    handler.press(1)
    assert handler.buttons[1].hold_time == 3


def test_press_twice_does_not_reset_hold_time(handler):
    handler.press(1)
    list(handler.get_events())
    list(handler.get_events())
    assert handler.buttons[1].hold_time == 3


def test_triggered_flag_resets_after_get_events(handler):
    handler.press(1)
    handler.release(1)
    events = list(handler.get_events())
    assert events[0].triggered
    assert not handler.buttons[1].triggered
    list(handler.get_events())
    assert not handler.buttons[1].triggered


def test_invalid_button_press_raises(handler):
    with pytest.raises(ValueError):
        handler.press(99)


def test_invalid_button_release_raises(handler):
    with pytest.raises(ValueError):
        handler.release(99)


def test_multiple_buttons_independent_state():
    handler = DummyInputHandler(event_map={1: 1, 2: 2})
    handler.press(1)
    handler.press(2)
    events = list(handler.get_events())
    buttons = {e.button: e for e in events}
    assert buttons[1].pressed
    assert buttons[2].pressed
    assert buttons[1].hold_time == 1
    assert buttons[2].hold_time == 1


def test_hold_duration_increases_over_time(handler):
    handler.press(1)
    inp = handler.buttons[1]
    handler.update_state(2.0)
    assert inp.hold_duration >= 2.0


def test_get_events_returns_clone(handler):
    handler.press(1)
    events = list(handler.get_events())
    inp = handler.buttons[1]
    assert events[0] is not inp
    assert events[0].button == inp.button
    assert events[0].value == inp.value


def test_virtual_stop_resets_press_time(handler):
    handler.press(1)
    inp = handler.buttons[1]
    list(handler.virtual_stop_events())
    assert inp.value == 1


def test_event_queue_handler_collects_events():
    queue = DummyEventQueueHandler()
    handler1 = DummyInputHandler(event_map={1: 1})
    handler2 = DummyInputHandler(event_map={2: 2})
    queue._inputs = {"player1": {1: handler1}, "player2": {2: handler2}}
    handler1.press(1)
    handler2.press(2)
    events = list(queue.process_events())
    buttons = {e.button for e in events}
    assert 1 in buttons
    assert 2 in buttons
