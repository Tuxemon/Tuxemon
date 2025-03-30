# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest import TestCase
from unittest.mock import MagicMock

from tuxemon.db import MissionStatus
from tuxemon.mission import Mission, MissionManager, MissionProgress


class TestMissionManager(TestCase):
    def test_init(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        self.assertEqual(mission_manager.missions, [])

    def test_add_mission(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        mission = Mission()
        mission_manager.add_mission(mission)
        self.assertEqual(mission_manager.missions, [mission])

    def test_remove_mission(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        mission = Mission()
        mission_manager.add_mission(mission)
        mission_manager.remove_mission(mission)
        self.assertEqual(mission_manager.missions, [])

    def test_remove_mission_not_found(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        mission = Mission()
        with self.assertRaises(ValueError):
            mission_manager.remove_mission(mission)

    def test_find_mission(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        mission = Mission()
        mission.slug = "test_mission"
        mission_manager.add_mission(mission)
        found_mission = mission_manager.find_mission("test_mission")
        self.assertEqual(found_mission, mission)

    def test_find_mission_not_found(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        found_mission = mission_manager.find_mission("test_mission")
        self.assertIsNone(found_mission)

    def test_update_status(self):
        mission = Mission()
        mission.status = MissionStatus.pending
        mission.update_status(MissionStatus.completed)
        self.assertEqual(mission.status, MissionStatus.completed)

    def test_update_status_no_change(self):
        mission = Mission()
        mission.status = MissionStatus.pending
        mission.update_status(MissionStatus.pending)
        self.assertEqual(mission.status, MissionStatus.pending)

    def test_get_mission_count(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        self.assertEqual(mission_manager.get_mission_count(), 0)
        mission_manager.add_mission(Mission())
        self.assertEqual(mission_manager.get_mission_count(), 1)

    def test_check_all_prerequisites(self):
        character = MagicMock()
        mission_manager = MissionManager(character)
        mission = Mission()
        mission.prerequisites = [{"key": "value"}]
        mission_manager.add_mission(mission)

        character.game_variables = {"key": "value"}
        self.assertTrue(mission_manager.check_all_prerequisites())

        character.game_variables = {"key": "wrong_value"}
        self.assertFalse(mission_manager.check_all_prerequisites())


class TestMission(TestCase):

    def test_check_required_monsters(self):
        mission = Mission()
        mission.required_monsters = ["potion", "lotion"]

        item1 = MagicMock()
        item1.slug = "potion"
        item2 = MagicMock()
        item2.slug = "lotion"

        character = MagicMock()
        character.find_item.side_effect = lambda slug: (
            item1 if slug == "potion" else item2 if slug == "lotion" else None
        )

        self.assertTrue(mission.check_required_items(character))

        character.find_item.side_effect = lambda slug: (
            item1 if slug == "potion" else None
        )
        self.assertFalse(mission.check_required_items(character))

    def test_check_required_monsters(self):
        mission = Mission()
        mission.required_monsters = ["monster1", "monster2"]

        monster1 = MagicMock()
        monster1.slug = "monster1"
        monster2 = MagicMock()
        monster2.slug = "monster2"

        character = MagicMock()
        character.find_monster.side_effect = lambda slug: (
            monster1
            if slug == "monster1"
            else monster2 if slug == "monster2" else None
        )

        self.assertTrue(mission.check_required_monsters(character))

        character.find_monster.side_effect = lambda slug: (
            monster1 if slug == "monster1" else None
        )
        self.assertFalse(mission.check_required_monsters(character))

    def test_get_progress(self):
        mission = Mission()

        # Test with no progress instances
        mission.progress = []
        character = MagicMock()
        character.game_variables = {"key": "value"}
        self.assertEqual(mission.get_progress(character), 0.0)
        # Test with progress instances that do not match
        mission.progress = [
            MissionProgress(
                game_variables={"key": "wrong_value"},
                completion_percentage=50.0,
            ),
        ]
        character.game_variables = {"key": "value"}
        self.assertEqual(mission.get_progress(character), 0.0)

        # Test with all matching instances
        mission.progress = [
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=100.0
            ),
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=50.0
            ),
        ]
        character.game_variables = {"key": "value"}
        self.assertEqual(mission.get_progress(character), 75.0)

        # Test with one matching and one not matching
        mission.progress = [
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=100.0
            ),
            MissionProgress(
                game_variables={"key": "wrong_value"},
                completion_percentage=50.0,
            ),
        ]
        character.game_variables = {"key": "value"}
        self.assertEqual(mission.get_progress(character), 100.0)

        # Test with all instances having zero completion
        mission.progress = [
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=0.0
            ),
            MissionProgress(
                game_variables={"key": "value"}, completion_percentage=0.0
            ),
        ]
        character.game_variables = {"key": "value"}
        self.assertEqual(mission.get_progress(character), 0.0)
