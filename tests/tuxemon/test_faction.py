# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.db import FactionRelationStatus, RankStep
from tuxemon.faction.faction import Faction


class TestFaction(unittest.TestCase):

    def setUp(self):
        self.faction = Faction()

    def test_init(self):
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

    def test_check_promotion(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 150}
        self.faction._rank_cache = {"test_npc": "test_rank1"}
        self.faction.reputation["test_npc"] = 250
        self.assertEqual(
            self.faction.check_promotion("test_npc", {}), "test_rank2"
        )

    def test_check_degradation_valid(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 150}
        self.faction._rank_cache = {"test_npc": "test_rank2"}

        self.assertEqual(
            self.faction.check_degradation("test_npc"), "test_rank1"
        )

    def test_check_degradation_to_none(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank1"),
            RankStep(threshold=200, title="test_rank2"),
        ]
        self.faction.reputation = {"test_npc": 50}
        self.faction._rank_cache = {"test_npc": "test_rank2"}

        self.assertEqual(self.faction.check_degradation("test_npc"), None)

    def test_can_be_promoted(self):
        self.faction.ranks = [
            RankStep(threshold=100, title="test_rank", requirement=None)
        ]
        self.faction.reputation = {"test_npc": 150}
        self.assertTrue(self.faction.can_be_promoted("test_npc", {}))
