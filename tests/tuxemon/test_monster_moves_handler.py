# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

from tuxemon.monster_dir.moves import MonsterMovesHandler


class TestMonsterMovesHandler(unittest.TestCase):

    def setUp(self):
        self.handler = MonsterMovesHandler()
        self.technique = MagicMock()
        self.moveset = [MagicMock()]
        self.moves = [MagicMock()]
        self.monster_id = UUID("123e4567-e89b-12d3-a456-426655440000")

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
        self.handler.learn(self.monster_id, self.technique)
        self.assertIn(self.technique, self.handler.moves)

    def test_forget(self):
        self.handler.learn(self.monster_id, self.technique)
        self.handler.forget(self.technique)
        self.assertNotIn(self.technique, self.handler.moves)

    def test_replace_move(self):
        technique1 = MagicMock()
        technique2 = MagicMock()
        self.handler.learn(self.monster_id, technique1)
        self.handler.replace_move(0, technique2)
        self.assertEqual(self.handler.moves[0], technique2)

    def test_set_moves(self):
        moveset = [
            MagicMock(
                level_learned=1,
                technique=MagicMock(slug="technique1"),
                evolution_stage_learned=None,
                learning_method="level_up",
            ),
            MagicMock(
                level_learned=2,
                technique=MagicMock(slug="technique2"),
                evolution_stage_learned=None,
                learning_method="level_up",
            ),
        ]
        with patch(
            "tuxemon.technique.technique.Technique.create"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            self.handler.set_moveset(moveset)
            self.handler.set_moves(self.monster_id, 2)
            self.assertEqual(len(self.handler.moves), 2)

    def test_update_moves(self):
        moveset = [
            MagicMock(
                level_learned=1,
                technique=MagicMock(slug="technique1"),
                evolution_stage_learned=None,
                learning_method="level_up",
            ),
            MagicMock(
                level_learned=2,
                technique=MagicMock(slug="technique2"),
                evolution_stage_learned=None,
                learning_method="level_up",
            ),
            MagicMock(
                level_learned=3,
                technique=MagicMock(slug="technique3"),
                evolution_stage_learned=None,
                learning_method="level_up",
            ),
        ]
        with patch(
            "tuxemon.technique.technique.Technique.create"
        ) as mock_create:
            mock_create.return_value = MagicMock()
            self.handler.set_moveset(moveset)
            self.handler.set_moves(self.monster_id, 2)
            new_techniques = self.handler.update_moves(3, 1)
            self.assertEqual(len(new_techniques), 1)

    def test_recharge_moves(self):
        self.handler.learn(self.monster_id, self.technique)
        self.handler.recharge_moves()

    def test_full_recharge_moves(self):
        self.handler.learn(self.monster_id, self.technique)
        self.handler.full_recharge_moves()

    def test_set_stats(self):
        self.handler.learn(self.monster_id, self.technique)
        self.handler.set_stats()

    def test_find_tech_by_id(self):
        self.handler.learn(self.monster_id, self.technique)
        found_technique = self.handler.find_tech_by_id(
            self.technique.instance_id
        )
        self.assertEqual(found_technique, self.technique)

    def test_has_moves(self):
        self.assertFalse(self.handler.has_moves())
        self.handler.learn(self.monster_id, self.technique)
        self.assertTrue(self.handler.has_moves())

    def test_has_move(self):
        self.handler.learn(self.monster_id, self.technique)
        self.assertTrue(self.handler.has_move(self.technique.slug))

    def test_get_moves(self):
        self.handler.learn(self.monster_id, self.technique)
        moves = self.handler.get_moves()
        self.assertIn(self.technique, moves)

    def test_can_forget_true(self):
        entry = MagicMock(technique="fireball", can_be_forgotten=True)
        self.handler.set_moveset([entry])
        self.assertTrue(self.handler.can_forget(MagicMock(slug="fireball")))

    def test_can_forget_false(self):
        entry = MagicMock(technique="icewall", can_be_forgotten=False)
        self.handler.set_moveset([entry])
        self.assertFalse(self.handler.can_forget(MagicMock(slug="icewall")))

    def test_remove_forced(self):
        self.technique.slug = "shockwave"
        self.handler.learn(self.monster_id, self.technique)
        removed = self.handler.remove_forced(self.technique)
        self.assertTrue(removed)
        self.assertNotIn(self.technique, self.handler.moves)

    def test_is_move_eligible_stage_mismatch(self):
        move = MagicMock(
            level_learned=3,
            evolution_stage_learned="stage2",
            technique="wave",
            learning_method="level_up",
        )
        result = self.handler.is_move_eligible(
            move=move, level=4, evolution_stage="basic"
        )
        self.assertFalse(result)

    def test_is_move_eligible_stage_match(self):
        move = MagicMock(
            level_learned=2,
            evolution_stage_learned="basic",
            technique="zap",
            learning_method="level_up",
        )
        result = self.handler.is_move_eligible(
            move=move, level=3, evolution_stage="basic"
        )
        self.assertTrue(result)
