# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from pygame.rect import Rect

from tuxemon.ui.combat_hud import CombatLayoutManager, MonsterUI, Side


class TestCombatLayoutManager(unittest.TestCase):
    def setUp(self):
        self.npc1 = MagicMock()
        self.npc1.name = "NPC1"
        self.npc1.is_player = False

        self.npc2 = MagicMock()
        self.npc2.name = "NPC2"
        self.npc2.is_player = False

        self.player_npc = MagicMock()
        self.player_npc.name = "Player"
        self.player_npc.is_player = True

        self.monster1 = MagicMock()
        self.monster1.name = "Monster1"

        self.monster2 = MagicMock()
        self.monster2.name = "Monster2"

        self.layouts = {
            self.npc1: {
                "home": [Rect(0, 0, 10, 10)],
                "monster_box_home": [Rect(5, 5, 10, 10)],
                "home0": [Rect(0, 0, 10, 10)],
                "monster_box_home0": [Rect(5, 5, 10, 10)],
                "home1": [Rect(10, 0, 10, 10)],
                "monster_box_home1": [Rect(15, 5, 10, 10)],
            },
            self.npc2: {
                "home": [Rect(20, 0, 10, 10)],
                "monster_box_home": [Rect(25, 5, 10, 10)],
                "home0": [Rect(20, 0, 10, 10)],
                "monster_box_home0": [Rect(25, 5, 10, 10)],
                "home1": [Rect(30, 0, 10, 10)],
                "monster_box_home1": [Rect(35, 5, 10, 10)],
            },
            self.player_npc: {
                "home": [Rect(40, 0, 10, 10)],
                "monster_box_home": [Rect(45, 5, 10, 10)],
                "home0": [Rect(40, 0, 10, 10)],
                "monster_box_home0": [Rect(45, 5, 10, 10)],
                "home1": [Rect(50, 0, 10, 10)],
                "monster_box_home1": [Rect(55, 5, 10, 10)],
            },
        }

        self.manager = CombatLayoutManager(self.layouts)

    def test_assign_player_vs_npc(self):
        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=False,
        )
        ui = self.manager._monster_ui[self.monster1]
        self.assertEqual(ui.slot_index, 1)
        self.assertEqual(ui.layout_key, "home")
        self.assertEqual(
            self.manager._positions[self.monster1][0], Side.PLAYER
        )

    def test_assign_npc_vs_npc(self):
        self.manager.assign(
            nr_players=2, npc=self.npc1, monster=self.monster1, is_double=False
        )
        self.manager.assign(
            nr_players=2, npc=self.npc2, monster=self.monster2, is_double=False
        )

        ui1 = self.manager._monster_ui[self.monster1]
        ui2 = self.manager._monster_ui[self.monster2]

        self.assertEqual(ui1.slot_index, 1)
        self.assertEqual(ui2.slot_index, 0)

        self.assertEqual(
            self.manager._positions[self.monster1][0], Side.PLAYER
        )
        self.assertEqual(
            self.manager._positions[self.monster2][0], Side.OPPONENT
        )

    def test_get_open_slot(self):
        slot = self.manager.get_open_slot(self.player_npc)
        self.assertEqual(slot, 0)

        self.manager._layout_keys[(self.player_npc, self.monster1)] = "home0"
        slot = self.manager.get_open_slot(self.player_npc)
        self.assertEqual(slot, 1)

    def test_get_rect_valid(self):
        rect = self.manager.get_rect(self.player_npc, "home")
        self.assertEqual(rect.topleft, (40, 0))

    def test_get_rect_missing_key(self):
        with self.assertRaises(ValueError):
            self.manager.get_rect(self.player_npc, "invalid_key")

    def test_assign_hud_and_get_hud(self):
        sprite = MagicMock()
        self.manager.assign_hud(self.monster1, sprite)
        self.assertIs(self.manager.get_hud(self.monster1), sprite)

    def test_delete_hud(self):
        sprite = MagicMock()
        sprite.kill = MagicMock()
        self.manager.assign_hud(self.monster1, sprite)
        self.manager.delete_hud(self.monster1)
        sprite.kill.assert_called_once()
        self.assertIsNone(self.manager.get_hud(self.monster1))

    def test_unassign(self):
        sprite = MagicMock()
        sprite.kill = MagicMock()
        icon = MagicMock()
        icon.kill = MagicMock()

        self.manager._monster_ui[self.monster1] = MonsterUI(
            slot_index=0,
            layout_key="home",
            hud_sprite=sprite,
            status_icons=[icon],
            feet_pos=(0, 0),
        )
        self.manager._positions[self.monster1] = (Side.PLAYER, 0)
        self.manager._layout_keys[(self.player_npc, self.monster1)] = "home"

        self.manager.unassign(self.player_npc, self.monster1)

        sprite.kill.assert_called_once()
        icon.kill.assert_called_once()
        self.assertNotIn(self.monster1, self.manager._monster_ui)
        self.assertNotIn(self.monster1, self.manager._positions)
        self.assertNotIn(
            (self.player_npc, self.monster1), self.manager._layout_keys
        )

    def test_reassign_monster_skips(self):
        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=False,
        )
        original_ui = self.manager._monster_ui[self.monster1]

        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=False,
        )
        reassigned_ui = self.manager._monster_ui[self.monster1]

        self.assertIs(original_ui, reassigned_ui)

    def test_get_index_default(self):
        index = self.manager.get_index(self.monster1)
        self.assertEqual(index, 0)

    def test_get_key_default(self):
        key = self.manager.get_key(self.player_npc, self.monster1)
        self.assertEqual(key, "home")

    def test_get_feet_position(self):
        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=False,
        )
        feet = self.manager.get_feet_position(self.player_npc, self.monster1)
        self.assertEqual(feet, (45, 5))

    def test_unassign_twice_safe(self):
        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=False,
        )
        self.manager.unassign(self.player_npc, self.monster1)
        self.manager.unassign(self.player_npc, self.monster1)

    def test_multiple_monsters_same_npc(self):
        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=False,
        )
        self.manager.assign(
            nr_players=1,
            npc=self.player_npc,
            monster=self.monster2,
            is_double=False,
        )

        index1 = self.manager.get_index(self.monster1)
        index2 = self.manager.get_index(self.monster2)

        self.assertEqual(index1, 1)
        self.assertEqual(index2, 1)

    def test_double_battle_layout_key(self):
        self.manager.assign(
            nr_players=2,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=True,
        )
        key = self.manager.get_key(self.player_npc, self.monster1)
        self.assertIn("home", key)

    def test_double_battle_slot_assignment(self):
        self.manager.assign(
            nr_players=2,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=True,
        )
        self.manager.assign(
            nr_players=2,
            npc=self.player_npc,
            monster=self.monster2,
            is_double=True,
        )

        ui1 = self.manager._monster_ui[self.monster1]
        ui2 = self.manager._monster_ui[self.monster2]

        self.assertIn(ui1.layout_key, ["home0", "home1"])
        self.assertIn(ui2.layout_key, ["home0", "home1"])
        self.assertNotEqual(ui1.slot_index, ui2.slot_index)

    def test_double_battle_feet_position(self):
        self.manager.assign(
            nr_players=2,
            npc=self.player_npc,
            monster=self.monster1,
            is_double=True,
        )
        feet = self.manager.get_feet_position(self.player_npc, self.monster1)

        self.assertIn(feet, [(45, 5), (55, 5)])

    def test_double_battle_npc_vs_npc(self):
        self.manager.assign(
            nr_players=2, npc=self.npc1, monster=self.monster1, is_double=True
        )
        self.manager.assign(
            nr_players=2, npc=self.npc2, monster=self.monster2, is_double=True
        )

        ui1 = self.manager._monster_ui[self.monster1]
        ui2 = self.manager._monster_ui[self.monster2]

        self.assertIn(ui1.layout_key, ["home0", "home1"])
        self.assertIn(ui2.layout_key, ["home0", "home1"])
        self.assertNotEqual(ui1.slot_index, ui2.slot_index)
