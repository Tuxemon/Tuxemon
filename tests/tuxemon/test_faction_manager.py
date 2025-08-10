# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock, patch

from tuxemon.db import FactionAlignment, FactionRelationStatus
from tuxemon.faction.faction import Faction
from tuxemon.faction.manager import FactionManager


class TestFactionManager(unittest.TestCase):

    def setUp(self):
        self.faction_manager = FactionManager()

    def test_init(self):
        self.assertEqual(self.faction_manager._factions, {})
        self.assertEqual(self.faction_manager._membership_cache, {})

    def test_load_core_factions(self):
        faction_slugs = ["faction1", "faction2"]
        faction1 = Faction()
        faction1.slug = "faction1"
        faction2 = Faction()
        faction2.slug = "faction2"

        with patch.object(Faction, "load_from_db") as mock_load:
            with patch.object(
                self.faction_manager, "register"
            ) as mock_register:
                self.faction_manager.load_core_factions(faction_slugs)

        self.assertEqual(mock_load.call_count, 2)
        self.assertEqual(mock_register.call_count, 2)

    def test_register(self):
        faction = Faction()
        faction.slug = "faction1"
        self.faction_manager.register(faction)
        self.assertIn(faction.slug, self.faction_manager._factions)

    def test_get(self):
        faction = Faction()
        faction.slug = "faction1"
        self.faction_manager.register(faction)
        self.assertEqual(self.faction_manager.get("faction1"), faction)

    def test_all_factions(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction2 = Faction()
        faction2.slug = "faction2"
        self.faction_manager.register(faction1)
        self.faction_manager.register(faction2)
        self.assertEqual(len(self.faction_manager.all_factions()), 2)

    def test_is_loaded(self):
        faction = Faction()
        faction.slug = "faction1"
        self.faction_manager.register(faction)
        self.assertTrue(self.faction_manager.is_loaded("faction1"))

    def test_get_factions_by_member(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.add_member("npc1")
        faction2 = Faction()
        faction2.slug = "faction2"
        self.faction_manager.register(faction1)
        self.faction_manager.register(faction2)
        self.assertEqual(
            len(self.faction_manager.get_factions_by_member("npc1")), 1
        )

    def test_clear_membership_cache(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.add_member("npc1")
        self.faction_manager.register(faction1)
        self.faction_manager.get_factions_by_member("npc1")
        self.faction_manager.clear_membership_cache("npc1")
        self.assertNotIn("npc1", self.faction_manager._membership_cache)

    def test_resolve_diplomacy(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.alignment = FactionAlignment.LAWFUL
        faction2 = Faction()
        faction2.slug = "faction2"
        faction2.alignment = FactionAlignment.LAWFUL
        self.faction_manager.register(faction1)
        self.faction_manager.register(faction2)
        self.faction_manager.resolve_diplomacy("faction1", "faction2")
        self.assertEqual(
            faction1.get_relation("faction2"), FactionRelationStatus.ALLY
        )

    def test_find_factions_by_alignment(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.alignment = FactionAlignment.LAWFUL
        faction2 = Faction()
        faction2.slug = "faction2"
        faction2.alignment = FactionAlignment.CHAOTIC
        self.faction_manager.register(faction1)
        self.faction_manager.register(faction2)
        self.assertEqual(
            len(
                self.faction_manager.find_factions_by_alignment(
                    FactionAlignment.LAWFUL
                )
            ),
            1,
        )

    def test_rank_npc_globally(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.add_member("npc1")
        self.faction_manager.register(faction1)
        self.assertIsNotNone(self.faction_manager.rank_npc_globally("npc1"))

    def test_get_state(self):
        save_data = {
            "factions_manager": {
                "faction1": {
                    "members": {"npc1": {"reputation": 10, "is_member": True}},
                    "public_reputation": 5,
                    "relations": {"faction2": "ALLY"},
                }
            }
        }

        faction1 = Faction()
        faction1.slug = "faction1"
        self.faction_manager.register(faction1)
        self.faction_manager.get_state(save_data)
        self.assertEqual(faction1.get_reputation("npc1"), 10)
        self.assertIn("npc1", faction1.members)
        self.assertEqual(faction1.public_reputation, 5)
        self.assertEqual(
            faction1.get_relation("faction2"), FactionRelationStatus.ALLY
        )

    def test_set_state(self):
        npc_manager = Mock()
        npc_manager.get_all_npc_slugs.return_value = ["npc1"]

        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.add_member("npc1")
        faction1.reputation["npc1"] = 10
        faction1.set_public_reputation(5)
        faction1.set_relation("faction2", FactionRelationStatus.ALLY)
        self.faction_manager.register(faction1)
        state = self.faction_manager.set_state(npc_manager)
        self.assertIn("factions_manager", state)
        faction_data = state["factions_manager"].get("faction1")
        self.assertIsNotNone(faction_data)
        member_data = faction_data.get("members", {}).get("npc1")
        self.assertEqual(member_data["reputation"], 10)
        self.assertTrue(member_data["is_member"])
        self.assertEqual(faction_data.get("public_reputation"), 5)
        self.assertIn("relations", faction_data)
        self.assertEqual(faction_data["relations"].get("faction2"), "ALLY")

    def test_load_core_factions_empty_list(self):
        self.faction_manager.load_core_factions([])
        self.assertEqual(self.faction_manager.all_factions(), [])

    def test_register_duplicate_faction(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        self.faction_manager.register(faction1)
        self.faction_manager.register(faction1)
        self.assertEqual(len(self.faction_manager.all_factions()), 1)

    def test_get_non_existent_faction(self):
        self.assertIsNone(self.faction_manager.get("faction1"))

    def test_all_factions_empty(self):
        self.assertEqual(self.faction_manager.all_factions(), [])

    def test_is_loaded_non_existent_faction(self):
        self.assertFalse(self.faction_manager.is_loaded("faction1"))

    def test_get_factions_by_member_empty(self):
        self.assertEqual(
            self.faction_manager.get_factions_by_member("npc1"), []
        )

    def test_clear_membership_cache_all(self):
        faction1 = Faction()
        faction1.slug = "faction1"
        faction1.add_member("npc1")
        self.faction_manager.register(faction1)
        self.faction_manager.get_factions_by_member("npc1")
        self.faction_manager.clear_membership_cache()
        self.assertEqual(self.faction_manager._membership_cache, {})
