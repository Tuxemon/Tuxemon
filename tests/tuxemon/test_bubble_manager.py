# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from pygame.surface import Surface

from tuxemon.map.view import BubbleManager
from tuxemon.npc import NPC


class TestBubbleManager(unittest.TestCase):

    def setUp(self):
        self.manager = BubbleManager()
        self.entity = MagicMock(spec=NPC)
        self.surface = MagicMock(spec=Surface)

    def test_init(self):
        self.assertEqual(self.manager.layer, 100)
        self.assertEqual(self.manager.offset_divisor, 10)
        self.assertEqual(self.manager._bubbles, {})

    def test_add_bubble(self):
        self.manager.add_bubble(self.entity, self.surface)
        self.assertIn(self.entity, self.manager._bubbles)
        self.assertEqual(self.manager._bubbles[self.entity], self.surface)

    def test_remove_bubble(self):
        self.manager.add_bubble(self.entity, self.surface)
        self.manager.remove_bubble(self.entity)
        self.assertNotIn(self.entity, self.manager._bubbles)

    def test_has_bubble(self):
        self.assertFalse(self.manager.has_bubble(self.entity))
        self.manager.add_bubble(self.entity, self.surface)
        self.assertTrue(self.manager.has_bubble(self.entity))

    def test_clear_all_bubbles(self):
        entity1 = MagicMock(spec=NPC)
        entity2 = MagicMock(spec=NPC)
        surface1 = MagicMock(spec=Surface)
        surface2 = MagicMock(spec=Surface)
        self.manager.add_bubble(entity1, surface1)
        self.manager.add_bubble(entity2, surface2)
        self.manager.clear_all_bubbles()
        self.assertEqual(self.manager._bubbles, {})
