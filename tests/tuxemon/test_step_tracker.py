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

    def test_milestone_dialogue_shown(self):
        self.tracker.trigger_milestone_event(100)
        self.tracker.show_milestone_dialogue(100)
        self.assertTrue(self.tracker.has_shown_milestone(100))


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
