# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.monster import Monster, MonsterStatusHandler
from tuxemon.npc import NPC
from tuxemon.states.combat.combat_classes import DamageTracker
from tuxemon.states.combat.reward_system import (
    RewardSystem,
    calculate_experience,
    calculate_experience_base,
    calculate_money,
)


class TestRewardSystem(unittest.TestCase):
    def setUp(self):
        self.loser = MagicMock(spec=Monster)
        self.loser.name = "pairagrin"
        self.loser.level = 5
        self.loser.money_modifier = 2.0
        self.loser.total_experience = 1000
        self.loser.experience_modifier = 1.5
        self.loser.status = MagicMock(spec=MonsterStatusHandler)
        self.loser.current_hp = 0
        self.loser.moves = MagicMock()

        self.winner = MagicMock(spec=Monster)
        self.winner.name = "rockitten"
        self.winner.status = MagicMock(spec=MonsterStatusHandler)
        self.winner.level = 5
        self.winner.moves = MagicMock()
        self.winner.current_hp = 50
        self.winner.owner = MagicMock(spec=NPC)
        self.winner.owner.isplayer = True
        self.winner.owner.monsters = [self.winner]
        self.winner.held_item = MagicMock(slug="xp_transmitter")

        self.damage_tracker = DamageTracker()
        self.damage_tracker.log_damage(self.winner, self.loser, 10, 1)

    def test_reward_system_winner(self):
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        self.assertEqual(len(rewards.winners), 1)
        self.assertEqual(rewards.winners[0].winner, self.winner)

    def test_reward_system_money(self):
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        awarded_money = calculate_money(self.loser, self.winner)
        self.assertEqual(rewards.winners[0].money, awarded_money)
        self.assertEqual(rewards.prize, awarded_money)

    def test_reward_system_experience(self):
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        awarded_exp, _ = calculate_experience(
            self.loser, self.winner, self.damage_tracker
        )
        self.assertEqual(rewards.winners[0].experience, awarded_exp)

    def test_reward_system_update(self):
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)
        self.assertTrue(rewards.update)

    def test_calculate_money_default_method(self):
        money = calculate_money(self.loser, self.winner)
        expected_money = int(self.loser.level * self.loser.money_modifier)
        self.assertEqual(money, expected_money)

    def test_calculate_experience_default_method(self):
        experience = calculate_experience(
            self.loser, self.winner, self.damage_tracker
        )
        expected_experience = int(
            (self.loser.total_experience // (self.loser.level))
            * self.loser.experience_modifier
        )
        self.assertEqual(experience[0], expected_experience)

    @patch("tuxemon.combat.alive_party")
    def test_calculate_experience_with_transmitter(self, alive_party_mock):
        mock_monsters = [
            MagicMock(
                spec=Monster, name="participant1", current_hp=50, status=[]
            ),
            MagicMock(
                spec=Monster, name="participant2", current_hp=50, status=[]
            ),
            MagicMock(
                spec=Monster, name="non_participant", current_hp=50, status=[]
            ),
        ]
        alive_party_mock.return_value = mock_monsters

        self.winner.held_item.get_item.return_value.slug = "xp_transmitter"

        experience = calculate_experience(
            self.loser, self.winner, self.damage_tracker
        )

        total_exp = calculate_experience_base(
            self.loser.total_experience,
            self.loser.level,
            self.loser.experience_modifier,
        )
        participants = self.damage_tracker.get_attackers(self.loser)
        participant_exp = total_exp // 2 // len(participants)

        self.assertEqual(experience[0], participant_exp)

    def test_calculate_experience_base(self):
        experience = calculate_experience_base(
            self.loser.total_experience,
            self.loser.level,
            self.loser.experience_modifier,
        )
        expected_experience = int(
            (self.loser.total_experience // (self.loser.level))
            * self.loser.experience_modifier
        )
        self.assertEqual(experience, expected_experience)

    @patch("tuxemon.combat.alive_party")
    def test_award_rewards_distribution(self, alive_party_mock):
        mock_monsters = [
            MagicMock(
                spec=Monster,
                give_experience=MagicMock(),
                moves=MagicMock(),
                level=5,
                status=MonsterStatusHandler(),
                current_hp=50,
                is_fainted=False,
            )
            for _ in range(3)
        ]
        alive_party_mock.return_value = mock_monsters

        self.winner.owner.monsters = mock_monsters

        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        self.assertEqual(len(rewards.winners), 1)
        self.assertEqual(rewards.winners[0].winner, self.winner)

        awarded_money = calculate_money(self.loser, self.winner)
        awarded_exp, _ = calculate_experience(
            self.loser, self.winner, self.damage_tracker
        )
        self.assertEqual(rewards.winners[0].money, awarded_money)
        self.assertEqual(rewards.winners[0].experience, awarded_exp)

        for monster in mock_monsters:
            monster.give_experience.assert_called()

    def test_award_rewards_no_winners(self):
        empty_tracker = DamageTracker()
        reward_system = RewardSystem(empty_tracker, is_trainer_battle=True)
        rewards = reward_system.award_rewards(self.loser)

        self.assertEqual(len(rewards.winners), 0)
        self.assertEqual(rewards.prize, 0)
        self.assertFalse(rewards.update)
        self.assertEqual(rewards.moves, [])
        self.assertEqual(rewards.messages, [])

    def test_award_rewards_no_new_moves(self):
        self.winner.moves.update_moves.return_value = []
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        self.assertEqual(rewards.moves, [])

    def test_award_rewards_multiple_move_updates(self):
        self.winner.moves.update_moves.return_value = ["Fireball"]
        second_winner = MagicMock(spec=Monster)
        second_winner.name = "rockitten"
        second_winner.level = 5
        second_winner.moves = MagicMock()
        second_winner.moves.update_moves.return_value = ["Ram"]
        second_winner.owner = self.winner.owner
        second_winner.status = MagicMock(spec=MonsterStatusHandler)
        second_winner.current_hp = 50
        second_winner.held_item = MagicMock(slug="default")

        self.damage_tracker.log_damage(second_winner, self.loser, 5, 1)

        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        self.assertIn("Fireball", rewards.moves)
        self.assertIn("Ram", rewards.moves)
        self.assertEqual(len(rewards.moves), 2)

    def test_award_rewards_with_held_item_modifier(self):
        self.winner.held_item.get_item.return_value.slug = "xp_booster"
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        self.assertGreater(rewards.winners[0].experience, 0)

    def test_award_rewards_non_player_monster(self):
        self.winner.owner.isplayer = False
        reward_system = RewardSystem(
            self.damage_tracker, is_trainer_battle=True
        )
        rewards = reward_system.award_rewards(self.loser)

        self.assertEqual(rewards.prize, 0)
        self.assertEqual(rewards.messages, [])
        self.assertFalse(rewards.update)
