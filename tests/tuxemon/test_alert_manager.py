# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time

import pytest
from pygame.font import Font
from pygame.rect import Rect

from tuxemon.event.eventbus import EventBus
from tuxemon.menu.alert import AlertManager
from tuxemon.scaling import DefaultScaling
from tuxemon.ui.text import TextArea
from tuxemon.user_config import CONFIG


@pytest.fixture
def font():
    return Font(None, 16)


@pytest.fixture
def text_area(font):
    return TextArea(
        font=font,
        font_color=(255, 255, 255),
        rect=Rect(0, 0, 200, 50),
        scaling=DefaultScaling(1),
    )


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def alert_manager(event_bus):
    return AlertManager(event_bus)


def test_alert_single_message(alert_manager, text_area):
    alert_manager.alert("Hello World", text_area)
    assert alert_manager.is_busy()
    assert text_area.text == "Hello World"


def test_alert_split_lines(alert_manager, text_area):
    msg = "Line1\nLine2\nLine3"
    alert_manager.alert(msg, text_area, split_lines=True)
    assert text_area.text == "Line1"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line2"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line3"


def test_alert_queue_multiple(alert_manager, text_area):
    alert_manager.alert("First", text_area)
    alert_manager.alert("Second", text_area)
    assert text_area.text == "First"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == "Second"


def test_callback_invoked(alert_manager, text_area):
    called = []

    def cb():
        called.append(True)

    alert_manager.alert("Message", text_area, callback=cb)
    alert_manager.dump_remaining_text(text_area)
    assert called


def test_callback_exception_handled(alert_manager, text_area):
    def bad_cb():
        raise ValueError("oops")

    alert_manager.alert("Message", text_area, callback=bad_cb)
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()


def test_is_dialog_complete(alert_manager, text_area):
    text_area.text = "abc"
    text_area.drawing_text = True
    assert not alert_manager.is_dialog_complete(text_area)
    alert_manager.dump_remaining_text(text_area)
    assert alert_manager.is_dialog_complete(text_area)


def test_current_message_none(alert_manager):
    assert alert_manager.current_message() is None


def test_current_message_with_lines(alert_manager, text_area):
    alert_manager.alert("Line1\nLine2", text_area, split_lines=True)
    assert alert_manager.current_message() == "Line2"


def test_update_progresses_text(alert_manager, text_area):
    alert_manager.character_delay = 0.01
    text_area.text = "abc"
    text_area.drawing_text = True
    alert_manager._time_accum = 0.05
    alert_manager.update(0.05)
    assert text_area.text == "abc"


def test_large_dt_consumes_all_text(alert_manager, text_area):
    alert_manager.alert("abcdef", text_area)
    alert_manager.character_delay = 0.01
    alert_manager.update(10.0)
    assert not text_area.drawing_text


def test_instant_dialog_speed(alert_manager, text_area):
    alert_manager.alert("Instant message", text_area, dialog_speed="instant")
    assert text_area.text == "Instant message"
    alert_manager.dump_remaining_text(text_area)
    assert alert_manager.is_dialog_complete(text_area)


def test_split_lines_instant_speed(alert_manager, text_area):
    msg = "Line1\nLine2\nLine3"
    alert_manager.alert(
        msg,
        dialog_speed="instant",
        text_area=text_area,
        split_lines=True,
    )
    assert text_area.text == "Line1"
    alert_manager.advance_dialog_line("instant", text_area)
    assert text_area.text == "Line2"
    alert_manager.advance_dialog_line("instant", text_area)
    assert text_area.text == "Line3"
    alert_manager.dump_remaining_text(text_area)
    assert alert_manager.is_dialog_complete(text_area)


def test_empty_queue_behavior(alert_manager):
    assert not alert_manager.is_busy()
    alert_manager._process_next_alert()
    assert not alert_manager.is_busy()


def test_busy_state_resets_after_alerts(alert_manager, text_area):
    alert_manager.alert("Test message", text_area)
    assert alert_manager.is_busy()
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()


def test_multiple_split_line_alerts(alert_manager, text_area):
    msg1 = "Line1a\nLine1b"
    msg2 = "Line2a\nLine2b"
    alert_manager.alert(msg1, text_area, split_lines=True)
    alert_manager.alert(msg2, text_area, split_lines=True)
    assert text_area.text == "Line1a"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line1b"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == "Line2a"


def test_empty_message_alert(alert_manager, text_area):
    alert_manager.alert("", text_area)
    assert text_area.text == ""
    alert_manager.dump_remaining_text(text_area)
    assert alert_manager.is_dialog_complete(text_area)


def test_alert_without_callback_advances_queue(alert_manager, text_area):
    alert_manager.alert("First message", text_area)
    alert_manager.alert("Second message", text_area)
    assert text_area.text == "First message"
    assert alert_manager.is_busy()
    alert_manager.dump_remaining_text(text_area)
    assert alert_manager.is_busy()
    assert text_area.text == "Second message"


def test_advance_without_split_state(alert_manager, text_area):
    alert_manager.alert("Single message", text_area, split_lines=False)
    alert_manager.dump_remaining_text(text_area)
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert not alert_manager.is_busy()
    assert text_area.text == "Single message"


def test_empty_split_lines_alert(alert_manager, text_area):
    alert_manager.alert("", text_area, split_lines=True)
    assert text_area.text == ""
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_mixed_split_and_single_alerts(alert_manager, text_area):
    split_msg = "Line1\nLine2"
    single_msg = "Final single line"
    alert_manager.alert(split_msg, text_area, split_lines=True)
    alert_manager.alert(single_msg, text_area, split_lines=False)
    assert text_area.text == "Line1"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line2"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == single_msg
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_callback_ordering(alert_manager, text_area):
    order = []

    def cb1():
        order.append("first_callback")

    def cb2():
        order.append("second_callback")

    alert_manager.alert("First message", text_area, callback=cb1)
    alert_manager.alert("Second message", text_area, callback=cb2)
    assert text_area.text == "First message"
    alert_manager.dump_remaining_text(text_area)
    assert "first_callback" in order
    assert text_area.text == "Second message"
    alert_manager.dump_remaining_text(text_area)
    assert order == ["first_callback", "second_callback"]
    assert not alert_manager.is_busy()


def test_update_with_no_active_area(alert_manager):
    alert_manager._active_area = None

    try:
        alert_manager.update(0.1)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"update() raised an exception unexpectedly: {e}")

    assert not alert_manager.is_busy()
    assert alert_manager._current_text_area() is None


def test_multiple_alerts_mixed_speeds_and_callbacks(alert_manager, text_area):
    order = []

    def cb1():
        order.append("callback1")

    def cb2():
        order.append("callback2")

    def cb3():
        order.append("callback3")

    msg_split = "LineA\nLineB"
    alert_manager.alert(
        "Instant alert",
        text_area,
        dialog_speed="instant",
        callback=cb1,
    )
    alert_manager.alert(
        "Normal alert",
        text_area,
        dialog_speed=CONFIG.dialog_speed,
        callback=cb2,
    )
    alert_manager.alert(
        msg_split,
        text_area,
        split_lines=True,
        callback=cb3,
    )
    assert text_area.text == "Instant alert"
    alert_manager.dump_remaining_text(text_area)
    assert "callback1" in order
    assert text_area.text == "Normal alert"
    alert_manager.dump_remaining_text(text_area)
    assert "callback2" in order
    assert text_area.text == "LineA"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "LineB"
    alert_manager.dump_remaining_text(text_area)
    assert "callback3" in order
    assert order == ["callback1", "callback2", "callback3"]
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_callback_exception_does_not_block_queue(alert_manager, text_area):
    order = []

    def good_cb1():
        order.append("good1")

    def bad_cb():
        raise RuntimeError("intentional failure")

    def good_cb2():
        order.append("good2")

    alert_manager.alert("First alert", text_area, callback=good_cb1)
    alert_manager.alert("Bad alert", text_area, callback=bad_cb)
    alert_manager.alert("Final alert", text_area, callback=good_cb2)
    alert_manager.dump_remaining_text(text_area)
    assert "good1" in order
    assert text_area.text == "Bad alert"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == "Final alert"
    alert_manager.dump_remaining_text(text_area)
    assert "good2" in order
    assert order == ["good1", "good2"]
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_current_message_during_alert_lifecycle(alert_manager, text_area):
    assert alert_manager.current_message() is None
    msg = "Line1\nLine2\nLine3"
    alert_manager.alert(msg, text_area, split_lines=True)
    assert text_area.text == "Line1"
    assert alert_manager.current_message() == "Line2"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line2"
    assert alert_manager.current_message() == "Line3"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line3"
    assert alert_manager.current_message() is None
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_dump_remaining_text_with_no_active_alert(alert_manager, text_area):
    assert not alert_manager.is_busy()
    assert alert_manager.current_message() is None

    try:
        alert_manager.dump_remaining_text(text_area)
    except Exception as e:  # noqa: BLE001
        pytest.fail(
            f"dump_remaining_text() raised an exception unexpectedly: {e}"
        )

    assert not alert_manager.is_busy()
    assert text_area.text == ""
    assert alert_manager.is_dialog_complete(text_area)


def test_multiple_split_alerts_back_to_back(alert_manager, text_area):
    msg1 = "Line1a\nLine1b\nLine1c"
    msg2 = "Line2a\nLine2b"
    msg3 = "Line3a\nLine3b\nLine3c\nLine3d"
    alert_manager.alert(msg1, text_area, split_lines=True)
    alert_manager.alert(msg2, text_area, split_lines=True)
    alert_manager.alert(msg3, text_area, split_lines=True)
    assert text_area.text == "Line1a"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line1b"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line1c"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == "Line2a"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line2b"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == "Line3a"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line3b"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line3c"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line3d"
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_update_with_large_dt_consumes_line_only(alert_manager, text_area):
    msg = "Hello World"
    alert_manager.alert(msg, text_area)
    alert_manager.character_delay = 0.01
    alert_manager.update(10.0)
    assert text_area.text == msg
    assert not text_area.drawing_text


def test_split_and_instant_alerts_mixed(alert_manager, text_area):
    alert_manager.alert("Line1\nLine2", text_area, split_lines=True)
    alert_manager.alert("Instant line", text_area, dialog_speed="instant")
    assert text_area.text == "Line1"
    alert_manager.advance_dialog_line(CONFIG.dialog_speed, text_area)
    assert text_area.text == "Line2"
    alert_manager.dump_remaining_text(text_area)
    assert text_area.text == "Instant line"
    alert_manager.dump_remaining_text(text_area)
    assert not alert_manager.is_busy()


def test_event_bus_publish_payload(alert_manager, text_area):
    published = []

    def fake_publish(event, payload):
        published.append((event, payload))

    alert_manager.event_bus.publish = fake_publish
    alert_manager.alert("Test message", text_area)
    assert published[0][0] == "DIALOG_STARTED"
    assert published[0][1]["message"] == "Test message"


def test_performance_with_many_alerts(alert_manager, text_area):
    for i in range(500):
        alert_manager.alert(f"Message {i}", text_area)

    processed = 0
    while alert_manager.is_busy():
        alert_manager.dump_remaining_text(text_area)
        processed += 1

    assert processed == 500
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)


def test_concurrent_alert_queueing(alert_manager, text_area):
    alert_manager.alert("Initial message", text_area)

    for i in range(50):
        alert_manager.alert(f"Concurrent message {i}", text_area)

    processed = 0
    while alert_manager.is_busy():
        alert_manager.dump_remaining_text(text_area)
        processed += 1

    assert processed == 51
    assert not alert_manager.is_busy()


def test_performance_with_many_alerts_and_timing(alert_manager, text_area):
    for i in range(500):
        alert_manager.alert(f"Message {i}", text_area)

    start = time.perf_counter()

    processed = 0
    while alert_manager.is_busy():
        alert_manager.dump_remaining_text(text_area)
        processed += 1

    end = time.perf_counter()
    elapsed = end - start

    assert processed == 500
    assert not alert_manager.is_busy()
    assert alert_manager.is_dialog_complete(text_area)
    assert elapsed < 1.0, f"Processing took too long: {elapsed:.3f}s"
