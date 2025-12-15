# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time
import unittest

import pygame

from tuxemon.event.eventbus import EventBus
from tuxemon.menu.alert import AlertManager
from tuxemon.prepare import CONFIG
from tuxemon.ui.text import TextArea


class TestAlertManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        font = pygame.font.Font(None, 16)
        self.text_area = TextArea(
            font=font,
            font_color=(255, 255, 255),
        )
        self.event_bus = EventBus()
        self.manager = AlertManager(self.event_bus)

    def test_alert_single_message(self):
        self.manager.alert("Hello World", self.text_area)
        self.assertTrue(self.manager.is_busy())
        self.assertEqual(self.text_area.text, "Hello World")

    def test_alert_split_lines(self):
        msg = "Line1\nLine2\nLine3"
        self.manager.alert(msg, self.text_area, split_lines=True)
        self.assertEqual(self.text_area.text, "Line1")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line2")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line3")

    def test_alert_queue_multiple(self):
        self.manager.alert("First", self.text_area)
        self.manager.alert("Second", self.text_area)
        self.assertEqual(self.text_area.text, "First")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, "Second")

    def test_callback_invoked(self):
        called = []

        def cb():
            called.append(True)

        self.manager.alert("Message", self.text_area, callback=cb)
        self.manager.dump_remaining_text(self.text_area)
        self.assertTrue(called)

    def test_callback_exception_handled(self):
        def bad_cb():
            raise ValueError("oops")

        self.manager.alert("Message", self.text_area, callback=bad_cb)
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())

    def test_is_dialog_complete(self):
        self.text_area.text = "abc"
        self.text_area.drawing_text = True
        self.assertFalse(self.manager.is_dialog_complete(self.text_area))
        self.manager.dump_remaining_text(self.text_area)
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_current_message_none(self):
        self.assertIsNone(self.manager.current_message())

    def test_current_message_with_lines(self):
        self.manager.alert("Line1\nLine2", self.text_area, split_lines=True)
        self.assertEqual(self.manager.current_message(), "Line2")

    def test_update_progresses_text(self):
        self.manager.character_delay = 0.01
        self.text_area.text = "abc"
        self.text_area.drawing_text = True
        self.manager._time_accum = 0.05
        self.manager.update(0.05)
        self.assertTrue(self.text_area.text, "abc")

    def test_large_dt_consumes_all_text(self):
        self.manager.alert("abcdef", self.text_area)
        self.manager.character_delay = 0.01
        self.manager.update(10.0)
        self.assertFalse(self.text_area.drawing_text)

    def test_instant_dialog_speed(self):
        self.manager.alert(
            "Instant message", self.text_area, dialog_speed="instant"
        )
        self.assertEqual(self.text_area.text, "Instant message")
        self.manager.dump_remaining_text(self.text_area)
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_split_lines_instant_speed(self):
        msg = "Line1\nLine2\nLine3"
        self.manager.alert(
            msg,
            dialog_speed="instant",
            text_area=self.text_area,
            split_lines=True,
        )
        self.assertEqual(self.text_area.text, "Line1")
        self.manager.advance_dialog_line("instant", self.text_area)
        self.assertEqual(self.text_area.text, "Line2")
        self.manager.advance_dialog_line("instant", self.text_area)
        self.assertEqual(self.text_area.text, "Line3")
        self.manager.dump_remaining_text(self.text_area)
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_empty_queue_behavior(self):
        self.assertFalse(self.manager.is_busy())
        self.manager._process_next_alert()
        self.assertFalse(self.manager.is_busy())

    def test_busy_state_resets_after_alerts(self):
        self.manager.alert("Test message", self.text_area)
        self.assertTrue(self.manager.is_busy())
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())

    def test_multiple_split_line_alerts(self):
        msg1 = "Line1a\nLine1b"
        msg2 = "Line2a\nLine2b"
        self.manager.alert(msg1, self.text_area, split_lines=True)
        self.manager.alert(msg2, self.text_area, split_lines=True)
        self.assertEqual(self.text_area.text, "Line1a")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line1b")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, "Line2a")

    def test_empty_message_alert(self):
        self.manager.alert("", self.text_area)
        self.assertEqual(self.text_area.text, "")
        self.manager.dump_remaining_text(self.text_area)
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_alert_without_callback_advances_queue(self):
        self.manager.alert("First message", self.text_area)
        self.manager.alert("Second message", self.text_area)
        self.assertEqual(self.text_area.text, "First message")
        self.assertTrue(self.manager.is_busy())
        self.manager.dump_remaining_text(self.text_area)
        self.assertTrue(self.manager.is_busy())
        self.assertEqual(self.text_area.text, "Second message")

    def test_advance_without_split_state(self):
        self.manager.alert("Single message", self.text_area, split_lines=False)
        self.manager.dump_remaining_text(self.text_area)
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertFalse(self.manager.is_busy())
        self.assertEqual(self.text_area.text, "Single message")

    def test_empty_split_lines_alert(self):
        self.manager.alert("", self.text_area, split_lines=True)
        self.assertEqual(self.text_area.text, "")
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_mixed_split_and_single_alerts(self):
        split_msg = "Line1\nLine2"
        single_msg = "Final single line"
        self.manager.alert(split_msg, self.text_area, split_lines=True)
        self.manager.alert(single_msg, self.text_area, split_lines=False)
        self.assertEqual(self.text_area.text, "Line1")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line2")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, single_msg)
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_callback_ordering(self):
        order = []

        def cb1():
            order.append("first_callback")

        def cb2():
            order.append("second_callback")

        self.manager.alert("First message", self.text_area, callback=cb1)
        self.manager.alert("Second message", self.text_area, callback=cb2)
        self.assertEqual(self.text_area.text, "First message")
        self.manager.dump_remaining_text(self.text_area)
        self.assertIn("first_callback", order)
        self.assertEqual(self.text_area.text, "Second message")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(order, ["first_callback", "second_callback"])
        self.assertFalse(self.manager.is_busy())

    def test_update_with_no_active_area(self):
        self.manager._active_area = None

        try:
            self.manager.update(0.1)
        except Exception as e:
            self.fail(f"update() raised an exception unexpectedly: {e}")

        self.assertFalse(self.manager.is_busy())
        self.assertIsNone(self.manager._current_text_area())

    def test_multiple_alerts_mixed_speeds_and_callbacks(self):
        order = []

        def cb1():
            order.append("callback1")

        def cb2():
            order.append("callback2")

        def cb3():
            order.append("callback3")

        msg_split = "LineA\nLineB"
        self.manager.alert(
            "Instant alert",
            self.text_area,
            dialog_speed="instant",
            callback=cb1,
        )
        self.manager.alert(
            "Normal alert",
            self.text_area,
            dialog_speed=CONFIG.dialog_speed,
            callback=cb2,
        )
        self.manager.alert(
            msg_split, self.text_area, split_lines=True, callback=cb3
        )
        self.assertEqual(self.text_area.text, "Instant alert")
        self.manager.dump_remaining_text(self.text_area)
        self.assertIn("callback1", order)
        self.assertEqual(self.text_area.text, "Normal alert")
        self.manager.dump_remaining_text(self.text_area)
        self.assertIn("callback2", order)
        self.assertEqual(self.text_area.text, "LineA")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "LineB")
        self.manager.dump_remaining_text(self.text_area)
        self.assertIn("callback3", order)
        self.assertEqual(order, ["callback1", "callback2", "callback3"])
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_callback_exception_does_not_block_queue(self):
        order = []

        def good_cb1():
            order.append("good1")

        def bad_cb():
            raise RuntimeError("intentional failure")

        def good_cb2():
            order.append("good2")

        self.manager.alert("First alert", self.text_area, callback=good_cb1)
        self.manager.alert("Bad alert", self.text_area, callback=bad_cb)
        self.manager.alert("Final alert", self.text_area, callback=good_cb2)
        self.manager.dump_remaining_text(self.text_area)
        self.assertIn("good1", order)
        self.assertEqual(self.text_area.text, "Bad alert")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, "Final alert")
        self.manager.dump_remaining_text(self.text_area)
        self.assertIn("good2", order)
        self.assertEqual(order, ["good1", "good2"])
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_current_message_during_alert_lifecycle(self):
        self.assertIsNone(self.manager.current_message())
        msg = "Line1\nLine2\nLine3"
        self.manager.alert(msg, self.text_area, split_lines=True)
        self.assertEqual(self.text_area.text, "Line1")
        self.assertEqual(self.manager.current_message(), "Line2")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line2")
        self.assertEqual(self.manager.current_message(), "Line3")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line3")
        self.assertIsNone(self.manager.current_message())
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_dump_remaining_text_with_no_active_alert(self):
        self.assertFalse(self.manager.is_busy())
        self.assertIsNone(self.manager.current_message())

        try:
            self.manager.dump_remaining_text(self.text_area)
        except Exception as e:
            self.fail(
                f"dump_remaining_text() raised an exception unexpectedly: {e}"
            )

        self.assertFalse(self.manager.is_busy())
        self.assertEqual(self.text_area.text, "")
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_multiple_split_alerts_back_to_back(self):
        msg1 = "Line1a\nLine1b\nLine1c"
        msg2 = "Line2a\nLine2b"
        msg3 = "Line3a\nLine3b\nLine3c\nLine3d"
        self.manager.alert(msg1, self.text_area, split_lines=True)
        self.manager.alert(msg2, self.text_area, split_lines=True)
        self.manager.alert(msg3, self.text_area, split_lines=True)
        self.assertEqual(self.text_area.text, "Line1a")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line1b")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line1c")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, "Line2a")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line2b")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, "Line3a")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line3b")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line3c")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line3d")
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_update_with_large_dt_consumes_line_only(self):
        msg = "Hello World"
        self.manager.alert(msg, self.text_area)
        self.manager.character_delay = 0.01
        self.manager.update(10.0)
        self.assertEqual(self.text_area.text, msg)
        self.assertFalse(self.text_area.drawing_text)

    def test_split_and_instant_alerts_mixed(self):
        self.manager.alert("Line1\nLine2", self.text_area, split_lines=True)
        self.manager.alert(
            "Instant line", self.text_area, dialog_speed="instant"
        )
        self.assertEqual(self.text_area.text, "Line1")
        self.manager.advance_dialog_line(CONFIG.dialog_speed, self.text_area)
        self.assertEqual(self.text_area.text, "Line2")
        self.manager.dump_remaining_text(self.text_area)
        self.assertEqual(self.text_area.text, "Instant line")
        self.manager.dump_remaining_text(self.text_area)
        self.assertFalse(self.manager.is_busy())

    def test_event_bus_publish_payload(self):
        published = []

        def fake_publish(event, payload):
            published.append((event, payload))

        self.manager.event_bus.publish = fake_publish
        self.manager.alert("Test message", self.text_area)
        self.assertEqual(published[0][0], "DIALOG_STARTED")
        self.assertEqual(published[0][1]["message"], "Test message")

    def test_performance_with_many_alerts(self):
        for i in range(500):
            self.manager.alert(f"Message {i}", self.text_area)

        processed = 0
        while self.manager.is_busy():
            self.manager.dump_remaining_text(self.text_area)
            processed += 1

        self.assertEqual(processed, 500)
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))

    def test_concurrent_alert_queueing(self):
        self.manager.alert("Initial message", self.text_area)

        for i in range(50):
            self.manager.alert(f"Concurrent message {i}", self.text_area)

        processed = 0
        while self.manager.is_busy():
            self.manager.dump_remaining_text(self.text_area)
            processed += 1

        self.assertEqual(processed, 51)
        self.assertFalse(self.manager.is_busy())

    def test_performance_with_many_alerts_and_timing(self):
        for i in range(500):
            self.manager.alert(f"Message {i}", self.text_area)

        start = time.perf_counter()

        processed = 0
        while self.manager.is_busy():
            self.manager.dump_remaining_text(self.text_area)
            processed += 1

        end = time.perf_counter()
        elapsed = end - start

        self.assertEqual(processed, 500)
        self.assertFalse(self.manager.is_busy())
        self.assertTrue(self.manager.is_dialog_complete(self.text_area))
        self.assertLess(
            elapsed, 1.0, f"Processing took too long: {elapsed:.3f}s"
        )
