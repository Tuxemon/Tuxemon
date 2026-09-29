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
def queue_and_handlers():
    queue = DummyEventQueueHandler()
    handler1 = DummyInputHandler(event_map={1: 1})
    handler2 = DummyInputHandler(event_map={2: 2})
    queue.set_input(player_id=0, index=0, input_handler=handler1)
    queue.set_input(player_id=1, index=0, input_handler=handler2)
    return queue, handler1, handler2


def test_process_events_single_press(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    events = list(queue.process_events())
    assert len(events) == 1
    assert events[0].button == 1
    assert events[0].pressed


def test_process_events_multiple_handlers(queue_and_handlers):
    queue, handler1, handler2 = queue_and_handlers
    handler1.press(1)
    handler2.press(2)
    events = list(queue.process_events())
    assert len(events) == 2
    buttons = {e.button for e in events}
    assert {1, 2}.issubset(buttons)


def test_release_controls_generates_virtual_stops(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    events = list(queue.release_controls())
    assert len(events) == 1
    assert events[0].button == 1
    assert events[0].value == 0


def test_release_controls_multiple_handlers(queue_and_handlers):
    queue, handler1, handler2 = queue_and_handlers
    handler1.press(1)
    handler2.press(2)
    events = list(queue.release_controls())
    assert len(events) == 2
    buttons = {e.button for e in events}
    assert {1, 2}.issubset(buttons)


def test_no_events_when_nothing_pressed(queue_and_handlers):
    queue, _, _ = queue_and_handlers
    assert list(queue.process_events()) == []


def test_no_virtual_stops_when_nothing_held(queue_and_handlers):
    queue, _, _ = queue_and_handlers
    assert list(queue.release_controls()) == []


def test_multiple_players_isolated_inputs(queue_and_handlers):
    queue, handler1, handler2 = queue_and_handlers
    handler1.press(1)
    handler2.press(2)
    events = list(queue.process_events())
    buttons = {e.button for e in events}
    assert {1, 2}.issubset(buttons)


def test_release_controls_after_multiple_frames(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    list(queue.process_events())
    list(queue.process_events())
    events = list(queue.release_controls())
    assert len(events) == 1
    assert events[0].button == 1
    assert events[0].value == 0


def test_repeated_release_controls_no_duplicates(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    events1 = list(queue.release_controls())
    events2 = list(queue.release_controls())
    assert len(events1) == 1
    assert len(events2) == 1


def test_press_release_press_cycle(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    list(queue.process_events())
    handler1.release(1)
    list(queue.process_events())
    handler1.press(1)
    events = list(queue.process_events())
    assert any(e.pressed for e in events)


def test_hold_time_accumulates_across_frames(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    for _ in range(5):
        list(queue.process_events())
    assert handler1.buttons[1].hold_time == 6


def test_triggered_flag_only_set_on_release(queue_and_handlers):
    queue, handler1, _ = queue_and_handlers
    handler1.press(1)
    list(queue.process_events())
    assert not handler1.buttons[1].triggered
    handler1.release(1)
    assert handler1.buttons[1].triggered


def test_clone_preserves_timestamp_and_state(queue_and_handlers):
    _, handler1, _ = queue_and_handlers
    handler1.press(1)
    original = handler1.buttons[1]
    clone = original.clone()
    assert clone.timestamp == original.timestamp
    assert clone.value == original.value
    assert clone.hold_time == original.hold_time
    assert clone.previous_value == original.previous_value


def test_event_order_consistency(queue_and_handlers):
    queue, handler1, handler2 = queue_and_handlers
    handler1.press(1)
    handler2.press(2)
    events = list(queue.process_events())
    assert events[0].button == 1
    assert events[1].button == 2
