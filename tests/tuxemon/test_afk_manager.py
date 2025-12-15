# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
# SPDX-License-Identifier: GPL-3.0
import unittest

from tuxemon.event import get_event_bus
from tuxemon.platform.afk_manager import AFKManager


class TestAFKManager(unittest.TestCase):
    def setUp(self):
        self.bus = get_event_bus()
        self.bus._listeners.clear()
        self.manager = AFKManager()
        self.events = []

        def listener(**kwargs):
            self.events.append(kwargs)

        def make_listener(event_name):
            def _listener(**kwargs):
                self.events.append((event_name, kwargs))

            return _listener

        self.bus.subscribe(
            "afk.threshold_reached", make_listener("afk.threshold_reached")
        )
        self.bus.subscribe("afk.reset", make_listener("afk.reset"))

    def test_add_threshold_valid(self):
        self.manager.add_threshold("warn", 10.0)
        self.assertEqual(len(self.manager.thresholds), 1)
        self.assertEqual(self.manager.thresholds[0].level, "warn")

    def test_add_threshold_invalid_duration(self):
        self.manager.add_threshold("bad", -5.0)
        self.assertEqual(len(self.manager.thresholds), 0)

    def test_add_threshold_duplicate(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.add_threshold("warn", 10.0)
        self.assertEqual(len(self.manager.thresholds), 1)
        self.assertEqual(self.manager.get_duration_by_level("warn"), 5.0)

    def test_remove_threshold(self):
        self.manager.add_threshold("warn", 10.0)
        removed = self.manager.remove_threshold("warn")
        self.assertTrue(removed)
        self.assertEqual(len(self.manager.thresholds), 0)

    def test_remove_threshold_nonexistent(self):
        removed = self.manager.remove_threshold("missing")
        self.assertFalse(removed)

    def test_modify_threshold(self):
        self.manager.add_threshold("warn", 10.0)
        modified = self.manager.modify_threshold("warn", 20.0)
        self.assertTrue(modified)
        self.assertEqual(self.manager.thresholds[0].duration, 20.0)

    def test_modify_threshold_nonexistent(self):
        modified = self.manager.modify_threshold("missing", 20.0)
        self.assertFalse(modified)

    def test_update_triggers_threshold(self):
        self.manager.add_threshold("warn", 5.0)
        result = self.manager.update(6.0)
        self.assertEqual(result, "warn")
        self.assertIn("warn", self.manager.active_levels)
        self.assertEqual(self.events[0][0], "afk.threshold_reached")

    def test_update_no_change(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.update(2.0)
        self.assertEqual(len(self.events), 0)
        self.assertIsNone(self.manager.current_level)

    def test_update_negative_time_delta(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.update(-3.0)
        self.assertEqual(self.manager.current_idle_time, 0.0)

    def test_update_triggers_highest_threshold(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.add_threshold("kick", 10.0)
        result = self.manager.update(12.0)
        self.assertEqual(result, "kick")
        self.assertIn("warn", self.manager.active_levels)
        self.assertIn("kick", self.manager.active_levels)

    def test_multiple_thresholds(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.add_threshold("kick", 10.0)
        self.manager.update(6.0)
        self.assertIn("warn", self.manager.active_levels)
        self.assertNotIn("kick", self.manager.active_levels)
        self.manager.update(5.0)
        self.assertIn("kick", self.manager.active_levels)

    def test_reset_clears_state(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.update(6.0)
        old_level = self.manager.reset()
        self.assertEqual(old_level, "warn")
        self.assertEqual(len(self.manager.active_levels), 0)
        self.assertEqual(self.events[-1][0], "afk.reset")

    def test_reset_when_not_afk(self):
        old_level = self.manager.reset()
        self.assertIsNone(old_level)
        self.assertEqual(self.manager.current_idle_time, 0.0)

    def test_current_level_property(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.add_threshold("kick", 10.0)
        self.manager.update(11.0)
        self.assertEqual(self.manager.current_level, "kick")

    def test_is_threshold_met(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.update(6.0)
        self.assertTrue(self.manager.is_threshold_met("warn"))
        self.assertFalse(self.manager.is_threshold_met("kick"))

    def test_get_duration_by_level(self):
        self.manager.add_threshold("warn", 5.0)
        self.assertEqual(self.manager.get_duration_by_level("warn"), 5.0)
        self.assertEqual(self.manager.get_duration_by_level("missing"), 0.0)

    def test_modify_threshold_resets_state(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.update(6.0)
        self.assertIn("warn", self.manager.active_levels)
        self.manager.modify_threshold("warn", 20.0)
        self.assertEqual(len(self.manager.active_levels), 0)
        self.assertEqual(self.manager._next_threshold_index, 0)

    def test_threshold_map_consistency(self):
        self.manager.add_threshold("warn", 5.0)
        self.assertEqual(self.manager.threshold_map["warn"], 5.0)
        self.manager.modify_threshold("warn", 15.0)
        self.assertEqual(self.manager.threshold_map["warn"], 15.0)
        self.manager.remove_threshold("warn")
        self.assertNotIn("warn", self.manager.threshold_map)

    def test_stress_game_loop_updates(self):
        self.manager.add_threshold("warn", 5.0)
        self.manager.add_threshold("kick", 10.0)
        self.manager.add_threshold("ban", 20.0)

        for second in range(25):
            result = self.manager.update(1.0)

            if second + 1 == 5:
                self.assertEqual(result, "warn")
            elif second + 1 == 10:
                self.assertEqual(result, "kick")
            elif second + 1 == 20:
                self.assertEqual(result, "ban")
            else:
                self.assertIsNone(result)

        self.assertIn("warn", self.manager.active_levels)
        self.assertIn("kick", self.manager.active_levels)
        self.assertIn("ban", self.manager.active_levels)
        self.assertEqual(self.manager.current_level, "ban")
