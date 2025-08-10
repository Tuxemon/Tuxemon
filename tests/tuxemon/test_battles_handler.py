# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.battle import Battle, BattlesHandler
from tuxemon.db import OutputBattle


class TestBattlesHandler(unittest.TestCase):

    def setUp(self) -> None:
        self.handler = BattlesHandler("player")

    def test_init(self):
        self.assertEqual(self.handler.get_battles(), [])

    def test_add_battle(self):
        battle = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        self.handler.add_battle(battle)
        self.assertEqual(len(self.handler.get_battles()), 1)

    def test_get_battles(self):
        battle1 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        battle2 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.lost,
                "steps": 5,
            }
        )
        self.handler.add_battle(battle1)
        self.handler.add_battle(battle2)
        self.assertEqual(len(self.handler.get_battles()), 2)

    def test_clear_battles(self):
        battle = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        self.handler.add_battle(battle)
        self.handler.clear_battles()
        self.assertEqual(len(self.handler.get_battles()), 0)

    def test_has_fought_and_outcome(self):
        battle = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        self.handler.add_battle(battle)
        self.assertTrue(
            self.handler.has_fought_and_outcome(OutputBattle.won.value, "npc")
        )

    def test_get_last_battle_outcome(self):
        battle1 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        battle2 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.lost,
                "steps": 5,
            }
        )
        self.handler.add_battle(battle1)
        self.handler.add_battle(battle2)
        self.assertEqual(
            self.handler.get_last_battle_outcome("npc"),
            OutputBattle.lost,
        )

    def test_get_battle_outcome_stats(self):
        battle1 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        battle2 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.lost,
                "steps": 5,
            }
        )
        self.handler.add_battle(battle1)
        self.handler.add_battle(battle2)
        stats = self.handler.get_battle_outcome_stats()
        self.assertEqual(stats[OutputBattle.won], 1)
        self.assertEqual(stats[OutputBattle.lost], 1)
        self.assertEqual(stats[OutputBattle.draw], 0)

    def test_get_battle_outcome_summary(self):
        battle1 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.won,
                "steps": 10,
            }
        )
        battle2 = Battle().from_save_data(
            {
                "fighter": "player",
                "opponent": "npc",
                "outcome": OutputBattle.lost,
                "steps": 5,
            }
        )
        self.handler.add_battle(battle1)
        self.handler.add_battle(battle2)
        summary = self.handler.get_battle_outcome_summary()
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["won"], 1)
        self.assertEqual(summary["lost"], 1)
        self.assertEqual(summary["draw"], 0)

    def test_record_battle(self):
        battle = self.handler.record_battle("npc", OutputBattle.draw, 3)
        self.assertEqual(len(self.handler.get_battles()), 1)
        self.assertEqual(battle.opponent, "npc")
        self.assertEqual(battle.outcome, OutputBattle.draw)
        self.assertEqual(battle.steps, 3)

    def test_get_last_battle(self):
        self.assertIsNone(self.handler.get_last_battle())
        battle1 = self.handler.record_battle("npc", OutputBattle.won, 10)
        battle2 = self.handler.record_battle("npc", OutputBattle.lost, 5)
        self.assertEqual(self.handler.get_last_battle(), battle2)

    def test_has_fought_and_outcome_invalid(self):
        self.handler.record_battle("npc", OutputBattle.won, 10)
        self.assertFalse(
            self.handler.has_fought_and_outcome("invalid_outcome", "npc")
        )

    def test_encode_decode_battle(self):
        self.handler.record_battle("npc", OutputBattle.won, 10)
        encoded = self.handler.encode_battle()
        new_handler = BattlesHandler("player")
        new_handler.decode_battle({"battles": encoded})
        self.assertEqual(len(new_handler.get_battles()), 1)
        self.assertEqual(
            new_handler.get_battles()[0].outcome, OutputBattle.won
        )

    def test_decode_battle_with_legacy_placeholder(self):
        legacy_data = {
            "battles": [
                {
                    "fighter": "player",
                    "opponent": "player",
                    "outcome": OutputBattle.draw,
                    "steps": 7,
                    "instance_id": "1234567890abcdef1234567890abcdef",
                }
            ]
        }
        handler = BattlesHandler("hero")
        handler.decode_battle(legacy_data)
        battle = handler.get_battles()[0]
        self.assertEqual(battle.fighter, "hero")
        self.assertEqual(battle.opponent, "hero")

    def test_decode_battle_empty(self):
        self.handler.decode_battle({})
        self.assertEqual(len(self.handler.get_battles()), 0)

    def test_record_battle_with_location_and_turns(self):
        battle = self.handler.record_battle(
            "npc", OutputBattle.won, 12, location="forest", turns=3
        )
        self.assertEqual(battle.location, "forest")
        self.assertEqual(battle.turns, 3)

    def test_get_battles_by_location(self):
        self.handler.record_battle(
            "npc1", OutputBattle.won, 5, location="cave"
        )
        self.handler.record_battle(
            "npc2", OutputBattle.lost, 8, location="cave"
        )
        self.handler.record_battle(
            "npc3", OutputBattle.draw, 3, location="forest"
        )
        grouped = self.handler.get_battles_by_location()
        self.assertEqual(len(grouped["cave"]), 2)
        self.assertEqual(len(grouped["forest"]), 1)
        self.assertEqual(grouped["forest"][0].opponent, "npc3")

    def test_default_location_and_turns(self):
        battle = self.handler.record_battle("npc", OutputBattle.draw, 4)
        self.assertEqual(battle.location, "")
        self.assertEqual(battle.turns, 1)

    def test_battle_outcome_summary_with_turns(self):
        self.handler.record_battle("npc1", OutputBattle.won, 5, turns=2)
        self.handler.record_battle("npc2", OutputBattle.lost, 8, turns=4)
        summary = self.handler.get_battle_outcome_summary()
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["won"], 1)
        self.assertEqual(summary["lost"], 1)
        self.assertEqual(summary["draw"], 0)
        self.assertEqual(summary["average_turns"], 3)  # (2+4)//2
