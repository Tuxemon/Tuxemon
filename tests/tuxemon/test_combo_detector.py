# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time
import unittest

from tuxemon.platform.combo_detector import ComboDetector, ComboProfile
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
        profile = ComboProfile(
            name="TestCombo",
            buttons=[buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[1, 1, 1, 1],
        )
        self.detector.add_combo(profile)
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

        profile1 = ComboProfile(
            name="TestCombo1",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=on_combo1,
            delays_s=[1, 1],
        )
        self.detector.add_combo(profile1)
        profile2 = ComboProfile(
            name="TestCombo2",
            buttons=[buttons.A, buttons.B],
            callback=on_combo2,
            delays_s=[1, 1],
        )
        self.detector.add_combo(profile2)

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))

        self.assertTrue(triggered_combo1, "Combo1 should trigger")

        self.detector.process_input(PlayerInput(buttons.A, now + 1.0))
        self.detector.process_input(PlayerInput(buttons.B, now + 1.2))

        self.assertTrue(triggered_combo2, "Combo2 should trigger")

    def test_combo_triggered_multiple_times(self):
        profile = ComboProfile(
            name="TestCombo",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[1, 1],
        )
        self.detector.add_combo(profile)

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
        profile = ComboProfile(
            name="TestCombo",
            buttons=[buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[1, 1, 1, 1],
        )
        self.detector.add_combo(profile)

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
        profile = ComboProfile(
            name="TestCombo",
            buttons=[buttons.LEFT, buttons.RIGHT, buttons.LEFT, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[1, 1, 1, 1],
        )
        self.detector.add_combo(profile)

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))
        self.detector.process_input(PlayerInput(buttons.LEFT, now + 0.4))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.6))

        self.assertTrue(
            self.triggered, "Combo should have triggered the callback"
        )

    def test_combo_removed(self):
        profile = ComboProfile(
            name="RemovableCombo",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=self.on_combo,
        )
        self.detector.add_combo(profile)
        removed = self.detector.remove_combo([buttons.LEFT, buttons.RIGHT])
        self.assertTrue(removed, "Combo should be removed successfully")

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))
        self.assertFalse(self.triggered, "Removed combo should not trigger")

    def test_priority_tiebreaker(self):
        triggered_low = False
        triggered_high = False

        def low_priority():
            nonlocal triggered_low
            triggered_low = True

        def high_priority():
            nonlocal triggered_high
            triggered_high = True

        profile_low = ComboProfile(
            name="LowPriority",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=low_priority,
            priority=1,
        )
        profile_high = ComboProfile(
            name="HighPriority",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=high_priority,
            priority=5,
        )
        self.detector.add_combo(profile_low)
        self.detector.add_combo(profile_high)

        now = time.time()
        self.detector.process_input(PlayerInput(buttons.LEFT, now))
        self.detector.process_input(PlayerInput(buttons.RIGHT, now + 0.2))

        self.assertTrue(triggered_high, "High priority combo should trigger")
        self.assertFalse(
            triggered_low, "Low priority combo should not trigger"
        )

    def test_combo_not_triggered_due_to_global_window(self):
        detector = ComboDetector(global_window_s=0.5)
        detector.add_combo(
            ComboProfile(
                name="WindowCombo",
                buttons=[buttons.LEFT, buttons.RIGHT],
                callback=self.on_combo,
            )
        )
        t_start = 10.0
        detector.process_input(PlayerInput(buttons.LEFT, timestamp=t_start))
        detector.process_input(
            PlayerInput(buttons.RIGHT, timestamp=t_start + 1.0)
        )
        self.assertFalse(
            self.triggered,
            "Combo should not trigger if global window exceeded",
        )

    def test_combo_not_triggered_due_to_delay(self):
        profile = ComboProfile(
            name="SlowCombo",
            buttons=[buttons.LEFT, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[0.2],
        )
        self.detector.add_combo(profile)

        t_start = 10.0
        self.detector.process_input(
            PlayerInput(buttons.LEFT, timestamp=t_start)
        )
        self.detector.process_input(
            PlayerInput(buttons.RIGHT, timestamp=t_start + 1.0)
        )

        self.assertFalse(
            self.triggered,
            "Combo should not trigger if individual step delay exceeded",
        )

    def test_three_button_combo_with_mixed_delays(self):
        profile = ComboProfile(
            name="TripleCombo",
            buttons=[buttons.LEFT, buttons.UP, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[0.5, 1.0],
        )
        self.detector.add_combo(profile)

        t_start = 20.0
        self.detector.process_input(
            PlayerInput(buttons.LEFT, timestamp=t_start)
        )
        self.detector.process_input(
            PlayerInput(buttons.UP, timestamp=t_start + 0.4)
        )
        self.detector.process_input(
            PlayerInput(buttons.RIGHT, timestamp=t_start + 1.3)
        )

        self.assertTrue(
            self.triggered, "Triple combo should trigger with valid delays"
        )

    def test_three_button_combo_fails_due_to_second_delay(self):
        profile = ComboProfile(
            name="TripleComboFail",
            buttons=[buttons.LEFT, buttons.UP, buttons.RIGHT],
            callback=self.on_combo,
            delays_s=[0.5, 1.0],
        )
        self.detector.add_combo(profile)

        t_start = 30.0
        self.detector.process_input(
            PlayerInput(buttons.LEFT, timestamp=t_start)
        )
        self.detector.process_input(
            PlayerInput(buttons.UP, timestamp=t_start + 0.4)
        )
        self.detector.process_input(
            PlayerInput(buttons.RIGHT, timestamp=t_start + 2.0)
        )

        self.assertFalse(
            self.triggered, "Combo should not trigger if second delay exceeded"
        )

    def test_priority_tiebreaker(self):
        def high_priority_cb():
            self.triggered = "high"

        def low_priority_cb():
            self.triggered = "low"

        self.detector.add_combo(
            ComboProfile(
                name="LowCombo",
                buttons=[buttons.LEFT, buttons.RIGHT],
                callback=low_priority_cb,
                priority=1,
            )
        )
        self.detector.add_combo(
            ComboProfile(
                name="HighCombo",
                buttons=[buttons.LEFT, buttons.RIGHT],
                callback=high_priority_cb,
                priority=5,
            )
        )
        t_start = 50.0
        self.detector.process_input(
            PlayerInput(buttons.LEFT, timestamp=t_start)
        )
        self.detector.process_input(
            PlayerInput(buttons.RIGHT, timestamp=t_start + 0.1)
        )
        self.assertEqual(
            self.triggered, "high", "Higher priority combo should win"
        )

    def test_combo_trigger_on_release(self):
        profile = ComboProfile(
            name="ReleaseCombo",
            buttons=[buttons.A, buttons.B],
            callback=self.on_combo,
            trigger_on_release=True,
        )
        self.detector.add_combo(profile)
        t_start = 40.0
        self.detector.process_input(
            PlayerInput(buttons.A, value=1, timestamp=t_start)
        )
        self.detector.process_input(
            PlayerInput(buttons.B, value=1, timestamp=t_start + 0.1)
        )
        release_event = PlayerInput(
            buttons.B, value=0, timestamp=t_start + 0.3
        )
        self.detector.process_input(release_event, hold_time=5)
        self.assertTrue(
            self.triggered, "Combo should trigger on release of final button"
        )
