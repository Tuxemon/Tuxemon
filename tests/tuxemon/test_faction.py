# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.db import FactionRelationStatus, RankStep
from tuxemon.faction.faction import Faction, satisfies_all_requirements


class TestFaction(unittest.TestCase):

    def setUp(self):
        self.faction = Faction()

    @patch("tuxemon.locale.T.translate", return_value="")
    def test_init(self, mock_translate):
        self.assertEqual(self.faction.slug, "")
        self.assertEqual(self.faction.name, "")
        self.assertEqual(self.faction.description, "")
        self.assertIsNone(self.faction.kind)
        self.assertIsNone(self.faction.alignment)
        self.assertIsNone(self.faction.badge_id)
        self.assertIsNone(self.faction.leader_char)
        self.assertEqual(self.faction.ranks, [])
        self.assertEqual(self.faction.members, [])
        self.assertEqual(self.faction.reputation, {})
        self.assertEqual(self.faction.relations, {})

    def test_get_rank_for_reputation(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.assertEqual(self.faction.get_rank_for_reputation(50), None)
        self.assertEqual(
            self.faction.get_rank_for_reputation(150), "test_rank1"
        )
        self.assertEqual(
            self.faction.get_rank_for_reputation(250), "test_rank2"
        )

    def test_get_current_rank(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 150}
        self.assertEqual(
            self.faction.get_current_rank("test_npc"), "test_rank1"
        )

    def test_get_relation(self):
        self.faction.relations = {"test_faction": FactionRelationStatus.ALLY}
        self.assertEqual(
            self.faction.get_relation("test_faction"),
            FactionRelationStatus.ALLY,
        )
        self.assertEqual(
            self.faction.get_relation("other_faction"),
            FactionRelationStatus.UNKNOWN,
        )

    def test_is_ally(self):
        self.faction.relations = {"test_faction": FactionRelationStatus.ALLY}
        self.assertTrue(self.faction.is_ally("test_faction"))
        self.assertFalse(self.faction.is_ally("other_faction"))

    def test_set_relation(self):
        self.faction.relations = {}
        self.faction.set_relation("test_faction", FactionRelationStatus.ALLY)
        self.assertEqual(
            self.faction.relations,
            {"test_faction": FactionRelationStatus.ALLY},
        )

    def test_modify_reputation(self):
        self.faction.reputation = {"test_npc": 100}
        self.faction.modify_reputation("test_npc", 50)
        self.assertEqual(self.faction.reputation, {"test_npc": 150})

    def test_get_reputation(self):
        self.faction.reputation = {"test_npc": 100}
        self.assertEqual(self.faction.get_reputation("test_npc"), 100)

    def test_add_member(self):
        self.faction.members = []
        self.faction.add_member("test_npc")
        self.assertEqual(self.faction.members, ["test_npc"])

    def test_remove_member(self):
        self.faction.members = ["test_npc"]
        self.faction.remove_member("test_npc")
        self.assertEqual(self.faction.members, [])

    def test_has_member(self):
        self.faction.members = ["test_npc"]
        self.assertTrue(self.faction.has_member("test_npc"))
        self.assertFalse(self.faction.has_member("other_npc"))

    def test_evaluate_rank_change_promotion(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 150}
        self.faction._rank_cache = {"test_npc": "test_rank1"}
        self.faction.reputation["test_npc"] = 250
        new_rank = self.faction.evaluate_rank_change("test_npc", {})
        self.assertEqual(new_rank, "test_rank2")
        self.assertEqual(
            self.faction.get_current_rank("test_npc"), "test_rank2"
        )

    def test_evaluate_rank_change_degradation_valid(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 150}
        self.faction._rank_cache = {"test_npc": "test_rank2"}
        new_rank = self.faction.evaluate_rank_change("test_npc", {})
        self.assertEqual(new_rank, "test_rank1")
        self.assertEqual(
            self.faction.get_current_rank("test_npc"), "test_rank1"
        )

    def test_evaluate_rank_change_degradation_to_none(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 50}
        self.faction._rank_cache = {"test_npc": "test_rank2"}
        new_rank = self.faction.evaluate_rank_change("test_npc", {})
        self.assertIsNone(new_rank)
        self.assertEqual(
            self.faction.get_current_rank("test_npc"), "test_rank2"
        )

    def test_can_be_promoted(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank", requirement=None)
        ]
        self.faction.reputation = {"test_npc": 150}
        self.assertTrue(self.faction.can_be_promoted("test_npc", {}))

    def test_update_decay_towards_baseline(self):
        self.faction._public_reputation = 30
        self.faction._neutral_baseline = 50
        self.faction.update(10.0)
        self.assertGreater(self.faction._public_reputation, 30)

    def test_update_removes_member_below_threshold(self):
        self.faction.ranks = [RankStep(threshold=100, title="Novice")]
        self.faction.add_member("npc1")
        self.faction.reputation["npc1"] = 10
        self.faction._decay_timer = 600.0
        self.faction.update(1.0)
        self.assertNotIn("npc1", self.faction.members)

    def test_power_level_calculation(self):
        self.faction.add_member("npc1")
        self.faction.reputation["npc1"] = 20
        self.assertEqual(self.faction.power_level, 20 + 1 * 10)

    def test_power_level_empty(self):
        self.assertEqual(self.faction.power_level, 0)

    def test_from_save_data_and_to_save_data_roundtrip(self):
        data = {"npc1": {"reputation": 10, "is_member": True}}
        relations = {"faction2": "ALLY"}
        self.faction.from_save_data(
            data, public_reputation=5, relations=relations
        )
        save = self.faction.to_save_data(["npc1"])
        self.assertEqual(save["members"]["npc1"]["reputation"], 10)
        self.assertEqual(save["public_reputation"], 5)
        self.assertEqual(save["relations"]["faction2"], "ALLY")

    def test_to_save_data_returns_none_for_empty_faction(self):
        self.assertIsNone(self.faction.to_save_data(["npc1"]))

    def test_set_relation_publishes_event(self):
        mock_bus = MagicMock()
        self.faction._event_bus = mock_bus
        self.faction.set_relation("factionX", FactionRelationStatus.ALLY)
        mock_bus.publish.assert_called()

    def test_add_member_publishes_event(self):
        mock_bus = MagicMock()
        self.faction._event_bus = mock_bus
        self.faction.add_member("npc1")
        mock_bus.publish.assert_called()

    def test_remove_member_publishes_event(self):
        mock_bus = MagicMock()
        self.faction._event_bus = mock_bus
        self.faction.members = ["npc1"]
        self.faction.remove_member("npc1")
        mock_bus.publish.assert_called()

    def test_rank_cache_invalidation_on_reputation_change(self):
        self.faction._rank_cache["npc1"] = "OldRank"
        self.faction.modify_reputation("npc1", 5)
        self.assertNotIn("npc1", self.faction._rank_cache)

    def test_promotion_with_unsatisfied_requirements(self):
        req = MagicMock()
        req.variables = [{"badge": "fire"}]
        self.faction.ranks = [
            RankStep(
                threshold=100,
                title="Champion",
                requirement={"variables": [{"badge": "fire"}]},
            )
        ]
        self.faction.reputation["npc1"] = 150
        game_vars = {"badge": "water"}
        self.assertFalse(self.faction.can_be_promoted("npc1", game_vars))

    def test_set_public_reputation_bounds(self):
        self.faction.set_public_reputation(-10)
        self.assertEqual(self.faction.public_reputation, 0)
        self.faction.set_public_reputation(999)
        self.assertEqual(
            self.faction.public_reputation, self.faction.MAX_PUBLIC_REPUTATION
        )

    def test_satisfies_all_requirements_true_and_false(self):
        game_vars = {"level": 10, "badge": "fire"}
        reqs = [{"level": 10}, {"badge": "fire"}]
        self.assertTrue(satisfies_all_requirements(reqs, game_vars))
        bad_reqs = [{"level": 20}]
        self.assertFalse(satisfies_all_requirements(bad_reqs, game_vars))
