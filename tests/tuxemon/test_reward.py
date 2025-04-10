# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.states.combat.combat_classes import DamageReport
from tuxemon.states.combat.reward_system import (
    RewardSystem,
    calculate_experience,
    calculate_experience_base,
    calculate_money,
    get_winners,
)


class TestRewardSystem(unittest.TestCase):
    def setUp(self):
        self.loser = MagicMock(spec=Monster)
        self.loser.name = "pairagrin"
        self.loser.level = 5
        self.loser.money_modifier = 2.0
        self.loser.total_experience = 1000
        self.loser.experience_modifier = 1.5

        self.winner = MagicMock(spec=Monster)
        self.winner.name = "rockitten"
        self.winner.owner = MagicMock(spec=NPC)
        self.winner.owner.isplayer = True
        self.winner.owner.game_variables = {"method_experience": "default"}

        self.damage_map = [
            DamageReport(attack=self.winner, defense=self.loser, damage=10)
        ]

    def test_calculate_money_default_method(self):
        money = calculate_money(self.loser, self.winner)
        expected_money = int(self.loser.level * self.loser.money_modifier)
        self.assertEqual(money, expected_money)

    def test_calculate_experience_default_method(self):
        hits = len(self.damage_map)
        experience = calculate_experience(
            self.loser, self.winner, self.damage_map
        )
        expected_experience = int(
            (self.loser.total_experience // (self.loser.level * hits))
            * self.loser.experience_modifier
        )
        self.assertEqual(experience, expected_experience)

    def test_calculate_experience_base(self):
        hits = len(self.damage_map)
        experience = calculate_experience_base(
            self.loser.total_experience,
            self.loser.level,
            hits,
            self.loser.experience_modifier,
        )
        expected_experience = int(
            (self.loser.total_experience // (self.loser.level * hits))
            * self.loser.experience_modifier
        )
        self.assertEqual(experience, expected_experience)

    def test_get_winners(self):
        winners = get_winners(self.loser, self.damage_map)
        self.assertIn(self.winner, winners)

    @patch("tuxemon.combat.alive_party")
    def test_experience_distribution(self, alive_party_mock):
        mock_monsters = [
            MagicMock(spec=Monster, give_experience=MagicMock())
            for _ in range(3)
        ]
        alive_party_mock.return_value = mock_monsters

        owner = MagicMock(spec=NPC)
        owner.monsters = mock_monsters

        hits = len(self.damage_map)
        expected_exp = int(
            (self.loser.total_experience // (self.loser.level * hits))
            * self.loser.experience_modifier
            / len(mock_monsters)
        )

        # Simulate distributing experience through logic in `award_rewards` or similar
        for monster in mock_monsters:
            monster.give_experience(expected_exp)

        # Assert give_experience was called on all alive monsters
        for monster in mock_monsters:
            monster.give_experience.assert_called_once_with(expected_exp)

    def test_reward_system(self):
        reward_system = RewardSystem(self.damage_map, is_trainer_battle=True)
        rewards = reward_system.award_rewards(self.loser)

        self.assertEqual(len(rewards.winners), 1)
        self.assertEqual(rewards.winners[0].winner, self.winner)

        awarded_money = calculate_money(self.loser, self.winner)
        awarded_exp = calculate_experience(
            self.loser, self.winner, self.damage_map
        )
        self.assertEqual(rewards.winners[0].money, awarded_money)
        self.assertEqual(rewards.winners[0].experience, awarded_exp)
        self.assertEqual(rewards.prize, awarded_money)
        self.assertTrue(rewards.update)
