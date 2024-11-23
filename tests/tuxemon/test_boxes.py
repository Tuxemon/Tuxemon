# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from uuid import uuid4

from tuxemon.boxes import MonsterBoxes
from tuxemon.monster import Monster
from tuxemon.states.pc_kennel import HIDDEN_LIST


class TestBoxes(unittest.TestCase):

    def setUp(self):
        self.monster_boxes = MonsterBoxes()
        self.monster1 = Monster()
        self.monster1.instance_id = uuid4()
        self.monster2 = Monster()
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
        self.monster_boxes.remove_monster(self.monster1)
        self.assertNotIn(
            self.monster1, self.monster_boxes.monster_boxes[self.box_id1]
        )

    def test_remove_monster_from(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.remove_monster_from(self.box_id1, self.monster1)
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
            self.monster_boxes.get_box_ids(), [self.box_id1, self.box_id2]
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
        HIDDEN_LIST.append(self.box_id1)
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_all_monsters_hidden(), [self.monster1]
        )

    def test_get_all_monsters_visible(self):
        HIDDEN_LIST.append(self.box_id1)
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.add_monster(self.box_id2, self.monster2)
        self.assertEqual(
            self.monster_boxes.get_all_monsters_visible(), [self.monster2]
        )

    def test_is_box_full(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.assertTrue(
            self.monster_boxes.is_box_full(self.box_id1, max_capacity=1)
        )
        self.monster_boxes.remove_monster_from(self.box_id1, self.monster1)
        self.assertFalse(
            self.monster_boxes.is_box_full(self.box_id1, max_capacity=1)
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
        self.monster_boxes.create_box(self.box_id1, "monster")
        self.assertIn(self.box_id1, self.monster_boxes.monster_boxes)

    def test_remove_box(self):
        self.monster_boxes.add_monster(self.box_id1, self.monster1)
        self.monster_boxes.remove_box(self.box_id1)
        self.assertNotIn(self.box_id1, self.monster_boxes.monster_boxes)

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
        self.assertTrue(self.monster_boxes.is_box_full(self.box_id1, 10))
        self.monster_boxes.create_and_merge_box(self.box_id1)
        self.assertIn(f"{self.box_id1}1", self.monster_boxes.get_box_ids())
        self.assertEqual(
            len(self.monster_boxes.get_monsters(f"{self.box_id1}1")), 10
        )
        self.assertEqual(len(self.monster_boxes.get_monsters(self.box_id1)), 0)
