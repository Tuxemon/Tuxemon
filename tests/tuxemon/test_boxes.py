# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from tuxemon.boxes import BoxMetadata, MonsterBoxes
from tuxemon.entity_dir.routing import RoutingPolicy
from tuxemon.monster import Monster


class TestBoxes(unittest.TestCase):

    def setUp(self):
        self.monster_boxes = MonsterBoxes()
        self.monster1 = MagicMock(spec=Monster)
        self.monster1.instance_id = uuid4()
        self.monster2 = MagicMock(spec=Monster)
        self.monster2.instance_id = uuid4()
        self.box_id1 = "box1"
        self.box_id2 = "box2"

    def test_add_monster(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertIn(self.box_id1, self.monster_boxes.monster_boxes)
        self.assertIn(
            self.monster1, self.monster_boxes.monster_boxes[self.box_id1]
        )

    def test_remove_monster(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.remove_from_box("monster", None, self.monster1)
        self.assertNotIn(
            self.monster1, self.monster_boxes.monster_boxes[self.box_id1]
        )

    def test_remove_monster_from(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.remove_from_box(
            "monster", self.box_id1, self.monster1
        )
        self.assertNotIn(
            self.monster1, self.monster_boxes.monster_boxes[self.box_id1]
        )

    def test_get_monsters_by_iid(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertEqual(
            self.monster_boxes.get_monsters_by_iid(self.monster1.instance_id),
            self.monster1,
        )

    def test_get_monsters(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id1, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_monsters(self.box_id1),
            [self.monster1, self.monster2],
        )

    def test_has_box(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertTrue(self.monster_boxes.has_box(self.box_id1, "monster"))

    def test_get_box_ids(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_box_ids("monster"),
            [self.box_id1, self.box_id2],
        )

    def test_get_box_size(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id1, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_box_size(self.box_id1, "monster"), 2
        )

    def test_get_box_name(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertEqual(
            self.monster_boxes.get_box_name(self.monster1.instance_id),
            self.box_id1,
        )

    def test_get_all_monsters(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_all_monsters(),
            [self.monster1, self.monster2],
        )

    def test_get_all_monsters_hidden(self):
        self.monster_boxes.create_box(
            self.box_id1, BoxMetadata(max_capacity=10, is_hidden=True)
        )
        self.monster_boxes.create_box(
            self.box_id2, BoxMetadata(max_capacity=10, is_hidden=False)
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_all_monsters_hidden(),
            [self.monster1],
        )

    def test_get_all_monsters_visible(self):
        self.monster_boxes.create_box(
            self.box_id1, BoxMetadata(max_capacity=10, is_hidden=True)
        )
        self.monster_boxes.create_box(
            self.box_id2, BoxMetadata(max_capacity=10, is_hidden=False)
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_all_monsters_visible(),
            [self.monster2],
        )

    def test_set_box_hidden_toggle(self):
        self.monster_boxes.create_box(
            self.box_id1, BoxMetadata(max_capacity=10, is_hidden=False)
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertEqual(
            self.monster_boxes.get_all_monsters_visible(),
            [self.monster1],
        )
        self.monster_boxes.set_box_hidden(self.box_id1, "monster", True)
        self.assertEqual(
            self.monster_boxes.get_all_monsters_hidden(),
            [self.monster1],
        )
        self.assertEqual(
            self.monster_boxes.get_all_monsters_visible(),
            [],
        )

    def test_is_box_full(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertTrue(
            self.monster_boxes.is_box_full(
                self.box_id1,
                "monster",
                RoutingPolicy("default", max_box_capacity=1),
            )
        )
        self.monster_boxes.remove_from_box(
            "monster", self.box_id1, self.monster1
        )
        self.assertFalse(
            self.monster_boxes.is_box_full(
                self.box_id1,
                "monster",
                RoutingPolicy("default", max_box_capacity=1),
            )
        )

    def test_move_monster(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.move_monster(
            self.box_id1, self.box_id2, self.monster1
        )
        self.assertIn(
            self.monster1, self.monster_boxes.monster_boxes[self.box_id2]
        )

    def test_merge_boxes(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id1, self.monster2)
        self.monster_boxes.merge_boxes(self.box_id1, self.box_id2)
        self.assertEqual(self.monster_boxes.get_monsters(self.box_id1), [])
        self.assertEqual(
            self.monster_boxes.get_monsters(self.box_id2),
            [self.monster1, self.monster2],
        )

    def test_create_box(self):
        self.monster_boxes.create_box(self.box_id1)
        self.assertIn(self.box_id1, self.monster_boxes.monster_boxes)

    def test_remove_box_forced(self):
        self.monster_boxes.create_box(self.box_id1)
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.remove_box(self.box_id1, force=True)
        self.assertNotIn(self.box_id1, self.monster_boxes.monster_boxes)

    def test_remove_box_not_forced_raises(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        with self.assertRaises(ValueError):
            self.monster_boxes.remove_box(self.box_id1, force=False)

    def test_swap_with_external_monster(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        external_monster = Monster()
        swapped_monster = self.monster_boxes.swap_with_external_monster(
            self.box_id1, self.monster1, external_monster
        )
        self.assertEqual(swapped_monster, self.monster1)
        self.assertEqual(
            self.monster_boxes.get_monsters(self.box_id1), [external_monster]
        )

    def test_swap_with_external_monster_not_found(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        external_monster = Monster()
        with self.assertRaises(ValueError):
            self.monster_boxes.swap_with_external_monster(
                self.box_id1, "non_existent_monster", external_monster
            )

    def test_swap_with_external_monster_invalid_box_id(self):
        external_monster = Monster()
        with self.assertRaises(ValueError):
            self.monster_boxes.swap_with_external_monster(
                "non_existent_box_id", self.monster1, external_monster
            )

    def test_swap_with_external_monster_by_iid(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        external_monster = Monster()
        swapped_monster = self.monster_boxes.swap_with_external_monster_by_iid(
            self.monster1.instance_id, external_monster
        )
        self.assertEqual(swapped_monster, self.monster1)
        self.assertEqual(
            self.monster_boxes.get_monsters(self.box_id1), [external_monster]
        )

    def test_swap_with_external_monster_by_iid_not_found(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        external_monster = Monster()
        with self.assertRaises(ValueError):
            self.monster_boxes.swap_with_external_monster_by_iid(
                "non_existent_monster", external_monster
            )

    def test_create_and_merge_box(self):
        for _ in range(10):
            self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertTrue(
            self.monster_boxes.is_box_full(
                self.box_id1,
                "monster",
                RoutingPolicy("default", max_box_capacity=10),
            )
        )
        self.monster_boxes.create_and_merge_box(self.box_id1, {})
        self.assertIn(
            f"{self.box_id1}1", self.monster_boxes.get_box_ids("monster")
        )
        self.assertEqual(
            len(self.monster_boxes.get_monsters(f"{self.box_id1}1")), 10
        )
        self.assertEqual(len(self.monster_boxes.get_monsters(self.box_id1)), 0)

    def test_get_total_monster_count(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(self.monster_boxes.get_total_monster_count(), 2)

    def test_find_monster_by_slug_in_boxes_found(self):
        self.monster1.slug = "test_slug"
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        result = self.monster_boxes.find_monster_by_slug_in_boxes("test_slug")
        self.assertEqual(result, (self.box_id1, self.monster1))

    def test_find_monster_by_slug_in_boxes_not_found(self):
        self.monster1.slug = "test_slug"
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        result = self.monster_boxes.find_monster_by_slug_in_boxes("other_slug")
        self.assertIsNone(result)

    def test_remove_monsters(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.monster_boxes.remove_monsters([self.monster1, self.monster2])
        self.assertEqual(self.monster_boxes.get_total_monster_count(), 0)

    def test_remove_box_force_false_empty(self):
        self.monster_boxes.create_box(self.box_id1)
        self.monster_boxes.remove_box(self.box_id1)
        self.assertNotIn(self.box_id1, self.monster_boxes.monster_boxes)

    def test_remove_box_force_false_non_empty_raises(self):
        self.monster_boxes.create_box(self.box_id1)
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        with self.assertRaises(ValueError):
            self.monster_boxes.remove_box(self.box_id1)

    def test_remove_box_force_true_non_empty(self):
        self.monster_boxes.create_box(self.box_id1)
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.remove_box(self.box_id1, force=True)
        self.assertNotIn(self.box_id1, self.monster_boxes.monster_boxes)

    def test_remove_box_non_existent_raises(self):
        with self.assertRaises(ValueError):
            self.monster_boxes.remove_box("does_not_exist")

    def test_attempt_add_monster_normal_case(self):
        policy = RoutingPolicy(name="test", max_box_capacity=5)
        self.monster_boxes.create_box(self.box_id1)
        result = self.monster_boxes.attempt_add_monster(
            self.monster1, policy, preferred_kennel=self.box_id1
        )
        self.assertTrue(result)
        self.assertIn(
            self.monster1, self.monster_boxes.get_monsters(self.box_id1)
        )

    def test_attempt_add_monster_box_full_with_overflow(self):
        policy = RoutingPolicy(
            name="test", max_box_capacity=1, overflow_kennel=self.box_id2
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.create_box(self.box_id2)
        result = self.monster_boxes.attempt_add_monster(
            self.monster2, policy, preferred_kennel=self.box_id1
        )
        self.assertTrue(result)
        self.assertIn(
            self.monster2, self.monster_boxes.get_monsters(self.box_id2)
        )

    def test_attempt_add_monster_box_full_auto_release(self):
        policy = RoutingPolicy(
            name="test", max_box_capacity=1, auto_release_if_box_full=True
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        result = self.monster_boxes.attempt_add_monster(
            self.monster2, policy, preferred_kennel=self.box_id1
        )
        self.assertFalse(result)
        self.assertNotIn(self.monster2, self.monster_boxes.get_all_monsters())

    def test_attempt_add_monster_overflow_missing_box(self):
        policy = RoutingPolicy(
            name="test", max_box_capacity=1, overflow_kennel="missing"
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        result = self.monster_boxes.attempt_add_monster(
            self.monster2, policy, preferred_kennel=self.box_id1
        )
        self.assertFalse(result)
        self.assertNotIn(self.monster2, self.monster_boxes.get_all_monsters())

    def test_attempt_add_monster_box_full_with_kennel_name_rules(self):

        policy = RoutingPolicy(
            name="test",
            max_box_capacity=1,
            kennel_name_rules={"suffix": "extra"},
        )

        monster1 = Monster()
        monster2 = Monster()
        monster2.instance_id = uuid4()

        self.monster_boxes.add_monster(self.box_id1, monster1)
        self.monster_boxes.attempt_add_monster(
            monster2, policy, preferred_kennel=self.box_id1
        )

        created_box_id = f"{self.box_id1}1extra"
        self.assertIn(
            created_box_id, self.monster_boxes.get_box_ids("monster")
        )
        monsters_in_new_box = self.monster_boxes.get_monsters(created_box_id)

        self.assertTrue(
            any(
                m.instance_id == monster2.instance_id
                for m in monsters_in_new_box
            )
        )

    def test_remove_box_cleans_metadata(self):
        self.monster_boxes.create_box(self.box_id1)
        self.monster_boxes.remove_box(self.box_id1)
        self.assertNotIn(
            self.box_id1,
            self.monster_boxes.metadata_manager._get_dict("monster"),
        )

    def test_create_box_with_metadata(self):
        meta = BoxMetadata(max_capacity=3, is_hidden=True)
        self.monster_boxes.create_box(self.box_id1, meta)
        capacity = self.monster_boxes.get_max_capacity(
            self.box_id1, "monster", RoutingPolicy("default")
        )
        self.assertEqual(capacity, 3)
        self.assertTrue(
            self.monster_boxes.is_box_hidden(self.box_id1, "monster")
        )

    def test_set_box_hidden_and_is_box_hidden(self):
        self.monster_boxes.create_box(
            self.box_id1, BoxMetadata(max_capacity=5, is_hidden=False)
        )
        self.assertFalse(
            self.monster_boxes.is_box_hidden(self.box_id1, "monster")
        )
        self.monster_boxes.set_box_hidden(self.box_id1, "monster", True)
        self.assertTrue(
            self.monster_boxes.is_box_hidden(self.box_id1, "monster")
        )

    def test_is_box_full_respects_metadata_capacity(self):
        self.monster_boxes.create_box(
            self.box_id1, BoxMetadata(max_capacity=1, is_hidden=False)
        )
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        policy = RoutingPolicy("default", max_box_capacity=10)
        self.assertTrue(
            self.monster_boxes.is_box_full(self.box_id1, "monster", policy)
        )
