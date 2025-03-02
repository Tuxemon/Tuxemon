# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import SeenStatus
from tuxemon.tuxepedia import (
    MonsterEntry,
    Tuxepedia,
    decode_tuxepedia,
    encode_tuxepedia,
)


class TestMonsterEntry(unittest.TestCase):

    def test_init(self):
        entry = MonsterEntry()
        self.assertEqual(entry.status, SeenStatus.seen)
        self.assertEqual(entry.appearance_count, 1)

    def test_init_with_status(self):
        entry = MonsterEntry(status=SeenStatus.caught)
        self.assertEqual(entry.status, SeenStatus.caught)
        self.assertEqual(entry.appearance_count, 1)

    def test_init_with_appearance_count(self):
        entry = MonsterEntry(appearance_count=5)
        self.assertEqual(entry.status, SeenStatus.seen)
        self.assertEqual(entry.appearance_count, 5)

    def test_init_with_status_and_appearance_count(self):
        entry = MonsterEntry(status=SeenStatus.caught, appearance_count=5)
        self.assertEqual(entry.status, SeenStatus.caught)
        self.assertEqual(entry.appearance_count, 5)

    def test_update_status(self):
        entry = MonsterEntry()
        entry.update_status(SeenStatus.caught)
        self.assertEqual(entry.status, SeenStatus.caught)

    def test_cannot_set_caught_to_seen(self):
        entry = MonsterEntry(status=SeenStatus.caught)
        entry.update_status(SeenStatus.seen)
        self.assertEqual(entry.status, SeenStatus.caught)

    def test_increment_appearance(self):
        entry = MonsterEntry()
        entry.increment_appearance()
        self.assertEqual(entry.appearance_count, 2)

    def test_reset_entry(self):
        entry = MonsterEntry(status=SeenStatus.caught, appearance_count=5)
        entry.reset_entry()
        self.assertEqual(entry.status, SeenStatus.seen)
        self.assertEqual(entry.appearance_count, 1)

    def test_get_state(self):
        entry = MonsterEntry(status=SeenStatus.caught, appearance_count=5)
        self.assertEqual(
            entry.get_state(),
            {"status": SeenStatus.caught, "appearance_count": 5},
        )


class TestTuxepedia(unittest.TestCase):

    def test_init(self):
        tuxepedia = Tuxepedia()
        self.assertEqual(tuxepedia.entries, {})

    def test_add_entry(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        self.assertIn("rockitten", tuxepedia.entries)
        self.assertEqual(
            tuxepedia.entries["rockitten"].status, SeenStatus.seen
        )
        self.assertEqual(tuxepedia.entries["rockitten"].appearance_count, 1)

    def test_add_entry_with_status(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten", status=SeenStatus.caught)
        self.assertIn("rockitten", tuxepedia.entries)
        self.assertEqual(
            tuxepedia.entries["rockitten"].status, SeenStatus.caught
        )
        self.assertEqual(tuxepedia.entries["rockitten"].appearance_count, 1)

    def test_get_total_monsters(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        tuxepedia.add_entry("nut")
        self.assertEqual(tuxepedia.get_total_monsters(), 2)

    def test_get_seen_count(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        tuxepedia.add_entry("nut", status=SeenStatus.caught)
        self.assertEqual(tuxepedia.get_seen_count(), 1)

    def test_get_caught_count(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten", status=SeenStatus.caught)
        tuxepedia.add_entry("nut", status=SeenStatus.caught)
        self.assertEqual(tuxepedia.get_caught_count(), 2)

    def test_get_most_frequent_monsters(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        tuxepedia.add_entry("nut")
        tuxepedia.add_entry("rockitten")
        self.assertEqual(
            tuxepedia.get_most_frequent_monsters(1), [("rockitten", 2)]
        )

    def test_get_monster_status_distribution(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        tuxepedia.add_entry("nut", status=SeenStatus.caught)
        distribution = tuxepedia.get_monster_status_distribution()
        self.assertEqual(distribution[SeenStatus.seen], 1)
        self.assertEqual(distribution[SeenStatus.caught], 1)

    def test_decode_tuxepedia(self):
        json_data = {
            "rockitten": {"status": SeenStatus.seen, "appearance_count": 1},
            "nut": {"status": SeenStatus.caught, "appearance_count": 1},
        }
        tuxepedia = Tuxepedia()
        tuxepedia = decode_tuxepedia(json_data)
        self.assertIn("rockitten", tuxepedia.entries)
        self.assertIn("nut", tuxepedia.entries)
        self.assertEqual(
            tuxepedia.entries["rockitten"].status, SeenStatus.seen
        )
        self.assertEqual(tuxepedia.entries["rockitten"].appearance_count, 1)
        self.assertEqual(tuxepedia.entries["nut"].status, SeenStatus.caught)
        self.assertEqual(tuxepedia.entries["nut"].appearance_count, 1)

    def test_encode_tuxepedia(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        tuxepedia.add_entry("nut", status=SeenStatus.caught)
        json_data = encode_tuxepedia(tuxepedia)
        self.assertIn("rockitten", json_data)
        self.assertIn("nut", json_data)
        self.assertEqual(json_data["rockitten"]["status"], SeenStatus.seen)
        self.assertEqual(json_data["rockitten"]["appearance_count"], 1)
        self.assertEqual(json_data["nut"]["status"], SeenStatus.caught)
        self.assertEqual(json_data["nut"]["appearance_count"], 1)

    def test_get_completeness(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        tuxepedia.add_entry("nut")
        self.assertAlmostEqual(tuxepedia.get_completeness(10), 0.2)
        self.assertAlmostEqual(tuxepedia.get_completeness(2), 1.0)
        self.assertAlmostEqual(tuxepedia.get_completeness(0), 0.0)

    def test_remove_entry(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("rockitten")
        self.assertIn("rockitten", tuxepedia.entries)
        tuxepedia.remove_entry("rockitten")
        self.assertNotIn("rockitten", tuxepedia.entries)
        with self.assertRaises(ValueError):
            tuxepedia.remove_entry("nut")

    def test_is_caught(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("nut", status=SeenStatus.caught)
        self.assertTrue(tuxepedia.is_caught("nut"))
        self.assertFalse(tuxepedia.is_caught("rockitten"))

    def test_is_seen(self):
        tuxepedia = Tuxepedia()
        tuxepedia.add_entry("nut")
        self.assertTrue(tuxepedia.is_seen("nut"))
        self.assertFalse(tuxepedia.is_seen("rockitten"))
        tuxepedia.add_entry("nut", status=SeenStatus.caught)
        self.assertFalse(tuxepedia.is_seen("nut"))
        self.assertTrue(tuxepedia.is_caught("nut"))
