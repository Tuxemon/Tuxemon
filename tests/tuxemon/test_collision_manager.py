# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon import prepare
from tuxemon.collision_manager import CollisionManager
from tuxemon.entity import Entity
from tuxemon.map import RegionProperties
from tuxemon.map_manager import MapManager
from tuxemon.npc_manager import NPCManager


class TestCollisionManager(unittest.TestCase):

    def setUp(self):
        self.map_manager = MagicMock(spec=MapManager)
        self.npc_manager = MagicMock(spec=NPCManager)
        self.collision_manager = CollisionManager(
            self.map_manager, self.npc_manager
        )

    def test_get_all_tile_properties(self):
        surface_map = {
            (0, 0): {"label1": 1.0, "label2": 2.0},
            (1, 1): {"label1": 3.0, "label3": 4.0},
        }
        self.map_manager.surface_map = surface_map
        result = self.collision_manager.get_all_tile_properties(
            surface_map, "label1"
        )
        self.assertEqual(result, [(0, 0), (1, 1)])

    def test_update_tile_property(self):
        surface_map = {
            (0, 0): {"label1": 1.0, "label2": 2.0},
            (1, 1): {"label1": 3.0, "label3": 4.0},
        }
        self.map_manager.surface_map = surface_map
        prepare.SURFACE_KEYS = ["label1", "label2", "label3"]
        self.collision_manager.update_tile_property("label1", 5.0)
        self.assertEqual(self.map_manager.surface_map[(0, 0)]["label1"], 5.0)
        self.assertEqual(self.map_manager.surface_map[(1, 1)]["label1"], 5.0)

    def test_all_tiles_modified(self):
        surface_map = {
            (0, 0): {"label1": 5.0, "label2": 2.0},
            (1, 1): {"label1": 5.0, "label3": 4.0},
        }
        self.map_manager.surface_map = surface_map
        prepare.SURFACE_KEYS = ["label1", "label2", "label3"]
        self.assertTrue(
            self.collision_manager.all_tiles_modified("label1", 5.0)
        )

    def test_check_collision_zones(self):
        collision_map = {
            (0, 0): RegionProperties([], [], [], None, "label1"),
            (1, 1): RegionProperties([], [], [], None, "label2"),
        }
        self.map_manager.collision_map = collision_map
        result = self.collision_manager.check_collision_zones(
            collision_map, "label1"
        )
        self.assertEqual(result, [(0, 0)])

    def test_add_collision(self):
        entity = MagicMock(spec=Entity)
        entity.is_player = True
        entity.tile_pos = (0, 0)
        region = RegionProperties([], [], [], None, "label1")
        self.map_manager.collision_map = {(0, 0): region}
        self.collision_manager.add_collision(entity, (0.0, 0.0))
        self.assertIsNotNone(self.map_manager.collision_map[(0, 0)].entity)

    def test_remove_collision(self):
        region = RegionProperties([], [], [], None, "label1")
        self.map_manager.collision_map = {(0, 0): region}
        self.collision_manager.remove_collision((0, 0))
        self.assertNotIn((0, 0), self.map_manager.collision_map)

    def test_add_collision_label(self):
        collision_map = {
            (0, 0): RegionProperties([], [], [], None, "label1"),
            (1, 1): RegionProperties([], [], [], None, "label2"),
        }
        self.map_manager.collision_map = collision_map
        self.collision_manager.add_collision_label("label1")
        self.assertEqual(self.map_manager.collision_map[(0, 0)].key, "label1")
        self.assertEqual(self.map_manager.collision_map[(1, 1)].key, "label2")

    def test_add_collision_position(self):
        self.map_manager.collision_map = {}
        self.collision_manager.add_collision_position("label1", (0, 0))
        self.assertIn((0, 0), self.map_manager.collision_map)
        self.assertEqual(self.map_manager.collision_map[(0, 0)].key, "label1")

    def test_remove_collision_label(self):
        collision_map = {
            (0, 0): RegionProperties([], [], [], None, "label1"),
            (1, 1): RegionProperties([], [], [], None, "label2"),
        }
        self.map_manager.collision_map = collision_map
        self.collision_manager.remove_collision_label("label1")
        self.assertEqual(self.map_manager.collision_map[(0, 0)].key, "label1")
        self.assertEqual(self.map_manager.collision_map[(1, 1)].key, "label2")

    def test_get_collision_map(self):
        self.map_manager.collision_map = {
            (0, 0): RegionProperties([], [], [], None, "label1")
        }
        self.map_manager.surface_map = {(0, 0): {"label1": 0.0}}
        npc = MagicMock(spec=Entity)
        npc.tile_pos = (0, 0)
        self.npc_manager.get_all_entities.return_value = [npc]
        collision_map = self.collision_manager.get_collision_map()
        self.assertIn((0, 0), collision_map)

    def test_get_region_properties(self):
        region = RegionProperties([], [], [], None, "label1")
        self.map_manager.collision_map = {(0, 0): region}
        properties = self.collision_manager._get_region_properties(
            (0, 0), "label1"
        )
        self.assertEqual(properties.key, "label1")
