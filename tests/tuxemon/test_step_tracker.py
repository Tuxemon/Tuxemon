# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.step_tracker import (
    StepTracker,
    StepTrackerManager,
    decode_steps,
    encode_steps,
)


class TestStepTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = StepTracker()

    def test_initial_state(self):
        self.assertEqual(self.tracker.steps, 0.0)
        self.assertEqual(self.tracker.countdown, 100.0)
        self.assertListEqual(self.tracker.milestones, [500, 250, 100, 50])

    def test_step_update(self):
        self.tracker.update_steps(10, 5)
        self.assertEqual(self.tracker.steps, 15.0)
        self.assertEqual(self.tracker.countdown, 85.0)

    def test_milestone_trigger(self):
        self.tracker.countdown = 49
        self.tracker.check_milestone_events()
        self.assertTrue(self.tracker.has_triggered_milestone(50))

    def test_milestone_dialogue_shown(self):
        self.tracker.trigger_milestone_event(100)
        self.tracker.show_milestone_dialogue(100)
        self.assertTrue(self.tracker.has_shown_milestone(100))

    def test_milestone_reached(self):
        self.tracker.update_steps(100, 0)
        self.assertTrue(self.tracker.has_reached_milestone(100))

    def test_step_update_individual(self):
        self.tracker.update_steps(10, 5)
        self.assertEqual(self.tracker.steps, 15.0)
        self.assertEqual(self.tracker.countdown, 85.0)

    def test_milestone_trigger_individual(self):
        self.tracker.countdown = 99
        self.tracker.check_milestone_events()
        self.tracker.trigger_milestone_event(100)
        self.assertTrue(self.tracker.has_triggered_milestone(100))

    def test_auto_reset_with_overflow(self):
        self.tracker.auto_reset = True
        self.tracker.countdown = 10
        self.tracker.update_steps(15, 0)
        self.assertEqual(self.tracker.countdown, 95.0)
        self.assertEqual(self.tracker.cycle_count, 1)

    def test_no_auto_reset(self):
        self.tracker.auto_reset = False
        self.tracker.countdown = 10
        self.tracker.update_steps(15, 0)
        self.assertEqual(self.tracker.countdown, 0)
        self.assertEqual(self.tracker.cycle_count, 0)

    def test_milestone_status_reset_on_cycle(self):
        self.tracker.countdown = 49
        self.tracker.check_milestone_events()
        self.assertTrue(self.tracker.has_triggered_milestone(50))
        self.tracker.reset_cycle()
        self.assertFalse(self.tracker.has_triggered_milestone(50))

    def test_update_when_countdown_zero(self):
        self.tracker.auto_reset = True
        self.tracker.countdown = 0
        self.tracker.update_steps(5, 5)
        self.assertEqual(self.tracker.steps, 10.0)
        self.assertEqual(self.tracker.countdown, 90.0)
        self.assertEqual(self.tracker.cycle_count, 1)

    def test_multiple_milestones_triggered(self):
        self.tracker.auto_reset = False
        self.tracker.countdown = 260
        self.tracker.update_steps(150, 100)
        for m in [250, 100, 50]:
            self.assertTrue(self.tracker.has_triggered_milestone(m))

    def test_serialization_cycle_count(self):
        self.tracker.cycle_count = 3
        self.tracker.auto_reset = False
        self.tracker.initial_countdown = 150
        manager = StepTrackerManager()
        manager.add_tracker("test", self.tracker)
        encoded = encode_steps(manager)
        decoded = decode_steps(encoded)
        decoded_tracker = decoded.get_tracker("test")
        self.assertEqual(decoded_tracker.cycle_count, 3)
        self.assertFalse(decoded_tracker.auto_reset)
        self.assertEqual(decoded_tracker.initial_countdown, 150)

    def test_decode_legacy_savegame_defaults(self):
        legacy_data = {
            "test": {
                "steps": 10.0,
                "countdown": 80.0,
                "milestones": [100, 50],
                "milestone_status": {
                    "50": {"triggered": True, "shown": False}
                },
            }
        }
        decoded = decode_steps(legacy_data)
        tracker = decoded.get_tracker("test")
        self.assertEqual(tracker.initial_countdown, 80.0)
        self.assertFalse(tracker.auto_reset)
        self.assertEqual(tracker.cycle_count, 0)

    def test_invalid_milestone_access(self):
        self.assertFalse(self.tracker.has_triggered_milestone(999))
        self.assertFalse(self.tracker.has_shown_milestone(999))

    def test_movement_equals_countdown(self):
        self.tracker.auto_reset = True
        self.tracker.countdown = 20
        self.tracker.update_steps(10, 10)
        self.assertEqual(self.tracker.countdown, 100.0)
        self.assertEqual(self.tracker.cycle_count, 1)

    def test_multiple_resets_in_one_update(self):
        self.tracker.auto_reset = True
        self.tracker.countdown = 10
        self.tracker.update_steps(300, 0)
        self.assertGreaterEqual(self.tracker.cycle_count, 2)

    def test_negative_movement(self):
        self.tracker.update_steps(-10, -5)
        self.assertEqual(self.tracker.countdown, 115.0)
        print(f"Countdown after negative movement: {self.tracker.countdown}")

    def test_empty_milestones(self):
        self.tracker.milestones = []
        self.tracker.countdown = 10
        self.tracker.update_steps(5, 5)
        self.assertEqual(self.tracker.milestone_status, {})

    def test_triggered_not_shown(self):
        self.tracker.countdown = 49
        self.tracker.check_milestone_events()
        self.assertTrue(self.tracker.has_triggered_milestone(50))
        self.assertFalse(self.tracker.has_shown_milestone(50))


class TestStepTrackerManager(unittest.TestCase):

    def setUp(self):
        self.manager = StepTrackerManager()
        self.tracker1 = StepTracker()
        self.tracker2 = StepTracker()
        self.manager.add_tracker("user1", self.tracker1)
        self.manager.add_tracker("user2", self.tracker2)

        assert "user1" in self.manager.trackers, "user1 tracker missing"
        assert "user2" in self.manager.trackers, "user2 tracker missing"

    def test_add_tracker(self):
        self.assertIn("user1", self.manager.trackers)

    def test_remove_tracker(self):
        self.manager.remove_tracker("user1")
        self.assertNotIn("user1", self.manager.trackers)

    def test_update_all(self):
        self.manager.update_all(20, 10)
        self.assertEqual(self.manager.get_tracker("user1").steps, 30.0)

    def test_encode_decode_steps(self):
        encoded_data = encode_steps(self.manager)
        decoded_manager = decode_steps(encoded_data)
        self.assertEqual(
            decoded_manager.get_tracker("user1").steps,
            self.manager.get_tracker("user1").steps,
        )

    def test_update_all_steps(self):
        self.manager.update_all(20, 10)
        self.assertEqual(self.manager.get_tracker("user1").steps, 30.0)
        self.assertEqual(self.manager.get_tracker("user2").steps, 30.0)

    def test_update_all_countdown(self):
        self.manager.update_all(50, 20)
        self.assertEqual(self.manager.get_tracker("user1").countdown, 30.0)
        self.assertEqual(self.manager.get_tracker("user2").countdown, 30.0)

    def test_milestone_not_triggered_globally(self):
        tracker = self.manager.get_tracker("user1")
        milestone = tracker.milestones[-1]
        self.manager.update_all(10, 10)
        self.assertFalse(
            self.manager.get_tracker("user1").has_triggered_milestone(
                milestone
            )
        )
        self.assertFalse(
            self.manager.get_tracker("user2").has_triggered_milestone(
                milestone
            )
        )

    def test_add_duplicate_tracker(self):
        with self.assertLogs(level="ERROR") as log:
            self.manager.add_tracker("user1", StepTracker())
            self.assertIn("already exists", log.output[0])

    def test_remove_nonexistent_tracker(self):
        with self.assertLogs(level="ERROR") as log:
            self.manager.remove_tracker("ghost")
            self.assertIn("does not exist", log.output[0])

    def test_get_nonexistent_tracker(self):
        tracker = self.manager.get_tracker("ghost")
        self.assertIsNone(tracker)
