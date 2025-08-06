# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import PlagueType
from tuxemon.monster_dir.plague import MonsterPlagueHandler


class TestMonsterPlagueHandler(unittest.TestCase):

    def setUp(self):
        self.handler = MonsterPlagueHandler()

    def test_init(self):
        self.assertEqual(self.handler.current_plagues, {})

    def test_infect(self):
        self.handler.infect("plague1")
        self.assertIn("plague1", self.handler.current_plagues)
        self.assertEqual(
            self.handler.get_plague_type("plague1"), PlagueType.infected
        )

    def test_inoculate(self):
        self.handler.inoculate("plague1")
        self.assertIn("plague1", self.handler.current_plagues)
        self.assertEqual(
            self.handler.get_plague_type("plague1"), PlagueType.inoculated
        )

    def test_is_infected(self):
        self.assertFalse(self.handler.is_infected())
        self.handler.infect("plague1")
        self.assertTrue(self.handler.is_infected())

    def test_remove_plague(self):
        self.handler.infect("plague1")
        self.handler.remove_plague("plague1")
        self.assertNotIn("plague1", self.handler.current_plagues)

    def test_has_plague(self):
        self.assertFalse(self.handler.has_plague("plague1"))
        self.handler.infect("plague1")
        self.assertTrue(self.handler.has_plague("plague1"))

    def test_get_plague_type(self):
        self.handler.infect("plague1")
        self.assertEqual(
            self.handler.get_plague_type("plague1"), PlagueType.infected
        )
        self.assertIsNone(self.handler.get_plague_type("plague2"))

    def test_get_infected_slugs(self):
        self.handler.infect("plague1")
        self.handler.inoculate("plague2")
        self.assertEqual(self.handler.get_infected_slugs(), ["plague1"])

    def test_is_infected_with(self):
        self.handler.infect("plague1")
        self.assertTrue(self.handler.is_infected_with("plague1"))
        self.assertFalse(self.handler.is_infected_with("plague2"))

    def test_is_inoculated_against(self):
        self.handler.inoculate("plague1")
        self.assertTrue(self.handler.is_inoculated_against("plague1"))
        self.assertFalse(self.handler.is_inoculated_against("plague2"))

    def test_clear_plagues(self):
        self.handler.infect("plague1")
        self.handler.inoculate("plague2")
        self.handler.clear_plagues()
        self.assertEqual(self.handler.current_plagues, {})
