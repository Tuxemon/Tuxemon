# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
import uuid
from unittest.mock import MagicMock

from tuxemon.npc_manager import NPCManager


class TestNPCManager(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = NPCManager()
        self.npc1 = MagicMock(slug="npc_1", instance_id=uuid.uuid4())
        self.npc2 = MagicMock(slug="npc_2", instance_id=uuid.uuid4())

    def test_add_npc(self) -> None:
        self.manager.add_npc(self.npc1)
        self.assertIn(self.npc1.slug, self.manager.npcs)
        self.assertEqual(self.manager.npcs[self.npc1.slug], self.npc1)

    def test_remove_npc(self) -> None:
        self.manager.add_npc(self.npc1)
        self.manager.remove_npc(self.npc1.slug)
        self.assertNotIn(self.npc1, self.manager.npcs)

    def test_npc_exists(self) -> None:
        self.manager.add_npc(self.npc1)
        self.assertTrue(self.manager.npc_exists(self.npc1.slug))
        self.assertFalse(self.manager.npc_exists("unknown_slug"))

    def test_add_npc_off_map(self) -> None:
        self.manager.add_npc_off_map(self.npc2)
        self.assertIn(self.npc2.slug, self.manager.npcs_off_map)
        self.assertEqual(self.manager.npcs_off_map[self.npc2.slug], self.npc2)

    def test_remove_npc_off_map(self) -> None:
        self.manager.add_npc_off_map(self.npc2)
        self.manager.remove_npc_off_map(self.npc2.slug)
        self.assertNotIn(self.npc2, self.manager.npcs_off_map)

    def test_clear_npcs(self) -> None:
        self.manager.add_npc(self.npc1)
        self.manager.add_npc_off_map(self.npc2)
        self.manager.clear_npcs()
        self.assertEqual(len(self.manager.npcs), 0)
        self.assertEqual(len(self.manager.npcs_off_map), 0)
