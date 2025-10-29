# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time
import unittest

from tuxemon.platform.combo_detector import ComboDetector
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput


class TestComboDetector(unittest.TestCase):

    def setUp(self):
        self.detector = ComboDetector()
        self.triggered = False

        def on_combo():
            self.triggered = True

        self.on_combo = on_combo

    def test_combo_not_triggered_with_wrong_sequence(self):
        self.detector.add_combo(
            [buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
            self.on_combo,
            max_delay_ms=1000,
        )

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(
            PlayerInput(buttons.UP, now + 0.2)
        )  # Wrong button
        self.detector.process_input(PlayerInput(buttons.LEFT, now + 0.4))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.6))

        self.assertFalse(
            self.triggered, "Combo should not trigger with incorrect sequence"
        )

    def test_multiple_combos_trigger_independently(self):
        triggered_combo1 = False
        triggered_combo2 = False

        def on_combo1():
            nonlocal triggered_combo1
            triggered_combo1 = True

        def on_combo2():
            nonlocal triggered_combo2
            triggered_combo2 = True

        self.detector.add_combo(
            [buttons.LEFT, buttons.RIGHT], on_combo1, max_delay_ms=1000
        )
        self.detector.add_combo(
            [buttons.A, buttons.B], on_combo2, max_delay_ms=1000
        )

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))

        self.assertTrue(triggered_combo1, "Combo1 should trigger")

        self.detector.process_input(PlayerInput(buttons.A, now + 1.0))
        self.detector.process_input(PlayerInput(buttons.B, now + 1.2))

        self.assertTrue(triggered_combo2, "Combo2 should trigger")

    def test_combo_triggered_multiple_times(self):
        self.detector.add_combo(
            [buttons.LEFT, buttons.RIGHT], self.on_combo, max_delay_ms=1000
        )

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))

        self.assertTrue(self.triggered, "Combo should trigger first time")

        # Reset flag and try again
        self.triggered = False
        self.detector.process_input(PlayerInput(buttons.LEFT, now + 2.0))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 2.2))

        self.assertTrue(self.triggered, "Combo should trigger second time")

    def test_combo_trigger_after_irrelevant_inputs(self):
        self.detector.add_combo(
            [buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
            self.on_combo,
            max_delay_ms=1000,
        )

        now = time.time()
        # Irrelevant buttons before the combo
        self.detector.process_input(PlayerInput(buttons.UP, now))
        self.detector.process_input(PlayerInput(buttons.DOWN, now + 0.1))
        self.detector.process_input(PlayerInput(buttons.SELECT, now + 0.2))

        # Actual combo sequence
        self.detector.process_input(PlayerInput(buttons.LEFT, now + 0.3))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.5))
        self.detector.process_input(PlayerInput(buttons.LEFT, now + 0.7))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.9))

        self.assertTrue(
            self.triggered, "Combo should trigger even after unrelated inputs"
        )

    def test_combo_trigger(self):
        self.detector.add_combo(
            [buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
            self.on_combo,
            max_delay_ms=1000,
        )

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))
        self.detector.process_input(PlayerInput(buttons.LEFT, now + 0.4))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.6))

        self.assertTrue(
            self.triggered, "Combo should have triggered the callback"
        )
