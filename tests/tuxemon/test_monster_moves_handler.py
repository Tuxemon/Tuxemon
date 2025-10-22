# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID

from tuxemon.db import EvolutionStage, LearningMethod
from tuxemon.monster_dir.moves import MonsterMovesHandler


class TestMonsterMovesHandler(unittest.TestCase):

    def setUp(self):
        self.handler = MonsterMovesHandler()
        self.technique = MagicMock()
        self.technique.slug = "techniqueX"
        self.technique.instance_id = UUID(
            "00000000-0000-0000-0000-000000000001"
        )
        self.moveset = [MagicMock()]
        self.moves = [MagicMock()]
        self.monster_id = UUID("123e4567-e89b-12d3-a456-426655440000")
        self.monster = MagicMock()
        self.monster.level = 3
        self.monster.stage = "basic"
        self.monster.iid = self.monster_id
        self.monster.slug = "testmon"

    def test_init(self):
        self.assertEqual(self.handler.moves, [])
        self.assertEqual(self.handler.moveset, [])
        handler = MonsterMovesHandler(self.moves, self.moveset)
        self.assertEqual(handler.moves, self.moves)
        self.assertEqual(handler.moveset, list(self.moveset))

    def test_set_moveset(self):
        self.handler.set_moveset(self.moveset)
        self.assertEqual(self.handler.moveset, list(self.moveset))

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_learn(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        self.assertIn(self.technique, self.handler.moves)

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_forget(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        self.handler.forget(self.technique)
        self.assertNotIn(self.technique, self.handler.moves)

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_replace_move(self, _mock_is_eligible):
        technique1 = MagicMock()
        technique2 = MagicMock()
        self.handler.learn(self.monster, technique1)
        self.handler.replace_move(0, technique2)
        self.assertEqual(self.handler.moves[0], technique2)

    def test_set_moves(self):
        moveset = [
            MagicMock(
                level_learned=1,
                technique="technique1",
                evolution_stage_learned=None,
                learning_method=LearningMethod.LEVEL_UP,
            ),
            MagicMock(
                level_learned=2,
                technique="technique2",
                evolution_stage_learned=None,
                learning_method=LearningMethod.LEVEL_UP,
            ),
        ]
        with (
            patch(
                "tuxemon.technique.technique.Technique.create"
            ) as mock_create,
            patch.object(
                MonsterMovesHandler,
                "is_eligible",
                side_effect=lambda m, slug, method=None: slug
                in {"technique1", "technique2"},
            ),
        ):
            mock_create.side_effect = lambda slug: MagicMock(slug=slug)
            self.handler.set_moveset(moveset)
            self.handler.set_moves(self.monster, 2)
            self.assertEqual(
                {m.slug for m in self.handler.moves},
                {"technique1", "technique2"},
            )

    def test_update_moves(self):
        moveset = [
            MagicMock(
                level_learned=1,
                technique="technique1",
                evolution_stage_learned=None,
                learning_method=LearningMethod.LEVEL_UP,
            ),
            MagicMock(
                level_learned=2,
                technique="technique2",
                evolution_stage_learned=None,
                learning_method=LearningMethod.LEVEL_UP,
            ),
            MagicMock(
                level_learned=3,
                technique="technique3",
                evolution_stage_learned=None,
                learning_method=LearningMethod.LEVEL_UP,
            ),
        ]
        with (
            patch(
                "tuxemon.technique.technique.Technique.create"
            ) as mock_create,
            patch.object(
                MonsterMovesHandler, "is_eligible", return_value=True
            ),
        ):
            mock_create.side_effect = lambda slug: MagicMock(slug=slug)
            self.handler.set_moveset(moveset)
            self.handler.set_moves(self.monster, 2)
            self.monster.level = 3
            new_techniques = self.handler.update_moves(self.monster, 1)
            self.assertEqual([t.slug for t in new_techniques], ["technique3"])

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_recharge_moves(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        self.handler.recharge_moves()

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_full_recharge_moves(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        self.handler.full_recharge_moves()

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_set_stats(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        self.handler.set_stats()

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_find_tech_by_id(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        found_technique = self.handler.find_tech_by_id(
            self.technique.instance_id
        )
        self.assertEqual(found_technique, self.technique)

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_has_moves(self, _mock_is_eligible):
        self.assertFalse(self.handler.has_moves())
        self.handler.learn(self.monster, self.technique)
        self.assertTrue(self.handler.has_moves())

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_has_move(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
        self.assertTrue(self.handler.has_move(self.technique.slug))

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_get_moves(self, _mock_is_eligible):
        self.handler.learn(self.monster, self.technique)
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

    @patch.object(MonsterMovesHandler, "is_eligible", return_value=True)
    def test_remove_forced(self, _mock_is_eligible):
        self.technique.slug = "shockwave"
        self.handler.learn(self.monster, self.technique)
        removed = self.handler.remove_forced(self.technique)
        self.assertTrue(removed)
        self.assertNotIn(self.technique, self.handler.moves)

    def test_is_eligible_stage_mismatch(self):
        move = MagicMock(spec=True)
        move.technique = "wave"
        move.level_learned = 3
        move.evolution_stage_learned = EvolutionStage.stage2
        move.learning_method = LearningMethod.LEVEL_UP

        self.handler.set_moveset([move])
        self.monster.level = 4
        self.monster.stage = EvolutionStage.basic

        result = self.handler.is_eligible(
            self.monster, "wave", method=LearningMethod.LEVEL_UP
        )
        self.assertFalse(result)

    def test_is_eligible_stage_match(self):
        move = MagicMock(spec=True)
        move.technique = "zap"
        move.level_learned = 2
        move.evolution_stage_learned = EvolutionStage.basic  # Use enum value
        move.learning_method = LearningMethod.LEVEL_UP

        self.handler.set_moveset([move])
        self.monster.level = 3
        self.monster.stage = EvolutionStage.basic  # Use enum value

        result = self.handler.is_eligible(
            self.monster, "zap", method=LearningMethod.LEVEL_UP
        )
        self.assertTrue(result)
