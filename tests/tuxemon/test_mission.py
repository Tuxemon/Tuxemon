# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import MissionStatus
from tuxemon.mission import Mission, MissionManager


class TestMissionManager(unittest.TestCase):
    def test_init(self):
        mission_manager = MissionManager()
        self.assertEqual(mission_manager.missions, [])

    def test_add_mission(self):
        mission_manager = MissionManager()
        mission = Mission()
        mission_manager.add_mission(mission)
        self.assertEqual(mission_manager.missions, [mission])

    def test_remove_mission(self):
        mission_manager = MissionManager()
        mission = Mission()
        mission_manager.add_mission(mission)
        mission_manager.remove_mission(mission)
        self.assertEqual(mission_manager.missions, [])

    def test_remove_mission_not_found(self):
        mission_manager = MissionManager()
        mission = Mission()
        with self.assertRaises(ValueError):
            mission_manager.remove_mission(mission)

    def test_find_mission(self):
        mission_manager = MissionManager()
        mission = Mission()
        mission.slug = "test_mission"
        mission_manager.add_mission(mission)
        found_mission = mission_manager.find_mission("test_mission")
        self.assertEqual(found_mission, mission)

    def test_find_mission_not_found(self):
        mission_manager = MissionManager()
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
