# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.monster import MonsterMovesHandler


class TestMonsterMovesHandler(unittest.TestCase):

    def setUp(self):
        self.handler = MonsterMovesHandler()
        self.technique = MagicMock()
        self.moveset = [MagicMock()]
        self.moves = [MagicMock()]

    def test_init(self):
        self.assertEqual(self.handler.moves, [])
        self.assertEqual(self.handler.moveset, [])
        handler = MonsterMovesHandler(self.moves, self.moveset)
        self.assertEqual(handler.moves, self.moves)
        self.assertEqual(handler.moveset, self.moveset)

    def test_set_moveset(self):
        self.handler.set_moveset(self.moveset)
        self.assertEqual(self.handler.moveset, self.moveset)

    def test_learn(self):
        self.handler.learn(self.technique)
        self.assertIn(self.technique, self.handler.moves)

    def test_forget(self):
        self.handler.learn(self.technique)
        self.handler.forget(self.technique)
        self.assertNotIn(self.technique, self.handler.moves)

    def test_replace_move(self):
        technique1 = MagicMock()
        technique2 = MagicMock()
        self.handler.learn(technique1)
        self.handler.replace_move(0, technique2)
        self.assertEqual(self.handler.moves[0], technique2)

    def test_set_moves(self):
        moveset = [
            MagicMock(level_learned=1, technique=MagicMock(slug="technique1")),
            MagicMock(level_learned=2, technique=MagicMock(slug="technique2")),
        ]
        with patch(
            "tuxemon.technique.technique.Technique.create"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            self.handler.set_moveset(moveset)
            self.handler.set_moves(2)
            self.assertEqual(len(self.handler.moves), 2)

    def test_update_moves(self):
        moveset = [
            MagicMock(level_learned=1, technique=MagicMock(slug="technique1")),
            MagicMock(level_learned=2, technique=MagicMock(slug="technique2")),
            MagicMock(level_learned=3, technique=MagicMock(slug="technique3")),
        ]
        with patch(
            "tuxemon.technique.technique.Technique.create"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            self.handler.set_moveset(moveset)
            self.handler.set_moves(2)
            new_techniques = self.handler.update_moves(3, 1)
            self.assertEqual(len(new_techniques), 1)

    def test_recharge_moves(self):
        self.handler.learn(self.technique)
        self.handler.recharge_moves()

    def test_full_recharge_moves(self):
        self.handler.learn(self.technique)
        self.handler.full_recharge_moves()

    def test_set_stats(self):
        self.handler.learn(self.technique)
        self.handler.set_stats()

    def test_find_tech_by_id(self):
        self.handler.learn(self.technique)
        found_technique = self.handler.find_tech_by_id(
            self.technique.instance_id
        )
        self.assertEqual(found_technique, self.technique)

    def test_has_moves(self):
        self.assertFalse(self.handler.has_moves())
        self.handler.learn(self.technique)
        self.assertTrue(self.handler.has_moves())

    def test_has_move(self):
        self.handler.learn(self.technique)
        self.assertTrue(self.handler.has_move(self.technique.slug))

    def test_get_moves(self):
        self.handler.learn(self.technique)
        moves = self.handler.get_moves()
        self.assertIn(self.technique, moves)
