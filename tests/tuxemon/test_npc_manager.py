# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tuxemon.npc_manager import NPCManager


class TestNPCManager(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = NPCManager()
        self.npc1 = MagicMock(
            slug="npc_1", instance_id=uuid4(), tile_pos=(1, 1)
        )
        self.npc2 = MagicMock(
            slug="npc_2", instance_id=uuid4(), tile_pos=(2, 2)
        )
        self.monster = MagicMock(instance_id=uuid4())
        self.npc1.monsters = [self.monster]
        self.npc2.monsters = []

    def test_add_and_get_npc(self) -> None:
        self.manager.add_npc(self.npc1)
        self.assertEqual(self.manager.get_npc("npc_1"), self.npc1)

    def test_add_and_get_npc_off_map(self) -> None:
        self.manager.add_npc_off_map(self.npc2)
        self.assertEqual(self.manager.get_npc_off_map("npc_2"), self.npc2)

    def test_get_npc_by_iid(self) -> None:
        self.manager.add_npc(self.npc1)
        self.assertEqual(
            self.manager.get_npc_by_iid(self.npc1.instance_id), self.npc1
        )
        self.assertIsNone(self.manager.get_npc_by_iid(uuid4()))

    def test_get_npc_off_map_by_iid(self) -> None:
        self.manager.add_npc_off_map(self.npc2)
        self.assertEqual(
            self.manager.get_npc_off_map_by_iid(self.npc2.instance_id),
            self.npc2,
        )

    def test_get_entity_pos(self) -> None:
        self.manager.add_npc(self.npc1)
        self.assertEqual(self.manager.get_entity_pos((1, 1)), self.npc1)
        self.assertIsNone(self.manager.get_entity_pos((9, 9)))

    @patch("tuxemon.networking.update_client")
    def test_update_npcs_calls_networking(self, mock_update_client) -> None:
        self.npc1.update_location = True
        self.npc1.final_move_dest = (3, 3)
        self.manager.add_npc(self.npc1)
        self.manager.update_npcs(0.1, MagicMock())
        mock_update_client.assert_called_once()

    @patch("tuxemon.networking.update_client")
    def test_update_npcs_off_map_calls_networking(
        self, mock_update_client
    ) -> None:
        self.npc2.update_location = True
        self.npc2.final_move_dest = (4, 4)
        self.manager.add_npc_off_map(self.npc2)
        self.manager.update_npcs_off_map(0.1, MagicMock())
        mock_update_client.assert_called_once()

    def test_clear_npcs_removes_non_persistent(self) -> None:
        self.npc1.persistence = False
        self.npc2.persistence = True
        self.manager.add_npc(self.npc1)
        self.manager.add_npc_off_map(self.npc2)
        self.manager.clear_npcs()
        self.assertNotIn("npc_1", self.manager.npcs)
        self.assertIn("npc_2", self.manager.npcs_off_map)

    def test_get_all_entities(self) -> None:
        self.manager.add_npc(self.npc1)
        entities = self.manager.get_all_entities()
        self.assertIn(self.npc1, entities)

    def test_get_all_monsters_and_by_iid(self) -> None:
        self.manager.add_npc(self.npc1)
        monsters = self.manager.get_all_monsters()
        self.assertIn(self.monster, monsters)
        self.assertEqual(
            self.manager.get_monster_by_iid(self.monster.instance_id),
            self.monster,
        )

    def test_add_clients_to_map(self) -> None:
        registry = {
            "client1": {"sprite": self.npc1, "map_name": "map_a"},
            "client2": {"sprite": self.npc2, "map_name": "map_b"},
        }
        self.manager.add_clients_to_map(registry, current_map="map_a")
        self.assertIn("npc_1", self.manager.npcs)
        self.assertIn("npc_2", self.manager.npcs_off_map)

    def test_get_all_npc_slugs(self) -> None:
        self.manager.add_npc(self.npc1)
        self.manager.add_npc_off_map(self.npc2)
        slugs = self.manager.get_all_npc_slugs(include_off_map=True)
        self.assertIn("npc_1", slugs)
        self.assertIn("npc_2", slugs)


class TestNPCManagerPersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = NPCManager()
        self.session = MagicMock()
        self.session.player.slug = "player_slug"
        self.session.client.get_map_name.return_value = "map_a"

        self.npc1 = MagicMock(
            slug="npc_1",
            instance_id=uuid4(),
            persistence=True,
            session=self.session,
        )
        self.npc1.get_state.return_value = MagicMock(
            player_slug="npc_1",
            player_name="NPC One",
            current_map="map_a",
        )

        self.npc2 = MagicMock(
            slug="npc_2",
            instance_id=uuid4(),
            persistence=True,
            session=self.session,
        )
        self.npc2.get_state.return_value = MagicMock(
            player_slug="npc_2",
            player_name="NPC Two",
            current_map="map_b",
        )

    def test_get_persistent_npc_states(self) -> None:
        self.manager.add_npc(self.npc1)
        self.manager.add_npc_off_map(self.npc2)
        states = self.manager.get_persistent_npc_states(self.session)
        slugs = [s.player_slug for s in states]
        self.assertIn("npc_1", slugs)
        self.assertIn("npc_2", slugs)
        self.assertNotIn("player_slug", slugs)

    @patch("tuxemon.npc_manager.NPC")
    def test_load_persistent_npc_states_on_current_map(self, MockNPC):
        fake_npc = MagicMock(slug="npc_1")
        MockNPC.return_value = fake_npc

        state = MagicMock(
            player_slug="npc_1", player_name="NPC One", current_map="map_a"
        )
        self.manager.load_persistent_npc_states(self.session, [state])

        self.assertIn("npc_1", self.manager.npcs)

    @patch("tuxemon.npc_manager.NPC")
    def test_load_persistent_npc_states_off_map(self, MockNPC):
        fake_npc = MagicMock(slug="npc_2")
        MockNPC.return_value = fake_npc

        state = MagicMock(
            player_slug="npc_2",
            player_name="NPC Two",
            current_map="map_b",
        )
        self.manager.load_persistent_npc_states(self.session, [state])
        self.assertIn("npc_2", self.manager.npcs_off_map)
        self.assertNotIn("npc_2", self.manager.npcs)

    def test_load_persistent_npc_states_skips_none_slug(self) -> None:
        state = MagicMock(
            player_slug=None,
            player_name="Nameless NPC",
            current_map="map_a",
        )
        self.manager.load_persistent_npc_states(self.session, [state])
        self.assertEqual(len(self.manager.npcs), 0)
        self.assertEqual(len(self.manager.npcs_off_map), 0)


class TestNPCManagerPersistenceIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = NPCManager()
        self.session = MagicMock()
        self.session.player.slug = "player_slug"
        self.session.client.get_map_name.return_value = "map_a"

        self.npc1 = MagicMock(
            slug="npc_1",
            instance_id=uuid4(),
            persistence=True,
            session=self.session,
        )
        self.npc1.get_state.return_value = MagicMock(
            player_slug="npc_1",
            player_name="NPC One",
            current_map="map_a",
        )

        self.npc2 = MagicMock(
            slug="npc_2",
            instance_id=uuid4(),
            persistence=True,
            session=self.session,
        )
        self.npc2.get_state.return_value = MagicMock(
            player_slug="npc_2",
            player_name="NPC Two",
            current_map="map_b",
        )

    @patch("tuxemon.npc_manager.NPC")
    def test_persistence_round_trip(self, MockNPC):
        fake_npc1 = MagicMock(slug="npc_1")
        fake_npc2 = MagicMock(slug="npc_2")
        MockNPC.side_effect = [fake_npc1, fake_npc2]

        self.manager.add_npc(self.npc1)
        self.manager.add_npc_off_map(self.npc2)

        states = self.manager.get_persistent_npc_states(self.session)
        self.assertEqual(len(states), 2)

        self.manager.npcs.clear()
        self.manager.npcs_off_map.clear()

        self.manager.load_persistent_npc_states(self.session, states)

        self.assertIn("npc_1", self.manager.npcs)
        self.assertIn("npc_2", self.manager.npcs_off_map)
        self.assertNotIn("npc_1", self.manager.npcs_off_map)
        self.assertNotIn("npc_2", self.manager.npcs)
