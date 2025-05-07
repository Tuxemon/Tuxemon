# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from typing import Any, Mapping
from unittest.mock import MagicMock

from tuxemon.relationship import (
    Connection,
    Relationships,
    decode_relationships,
    encode_relationships,
)


class TestConnection(unittest.TestCase):
    def test_connection_initialization(self):
        connection = Connection(
            relationship_type="friend",
            strength=75,
            steps=100,
            decay_rate=0.02,
            decay_threshold=1000,
        )
        self.assertEqual(connection.relationship_type, "friend")
        self.assertEqual(connection.strength, 75)
        self.assertEqual(connection.steps, 100)
        self.assertEqual(connection.decay_rate, 0.02)
        self.assertEqual(connection.decay_threshold, 1000)

    def test_update_steps(self):
        connection = Connection(relationship_type="friend")
        mock_npc = MagicMock(steps=200)
        connection.update_steps(mock_npc)
        self.assertEqual(connection.steps, 200)

    def test_apply_decay_no_decay(self):
        connection = Connection(
            relationship_type="friend",
            strength=75,
            steps=100,
            decay_threshold=500,
        )
        mock_npc = MagicMock(steps=400)
        connection.apply_decay(mock_npc)
        self.assertEqual(connection.strength, 75)

    def test_apply_decay_minimum_strength(self):
        connection = Connection(
            relationship_type="friend",
            strength=5,
            steps=0,
            decay_rate=0.5,
            decay_threshold=100,
        )
        mock_npc = MagicMock(steps=200)
        connection.apply_decay(mock_npc)
        self.assertEqual(connection.strength, 4)

    def test_apply_decay_maximum_strength(self):
        connection = Connection(
            relationship_type="friend",
            strength=95,
            steps=0,
            decay_rate=0.5,
            decay_threshold=100,
        )
        mock_npc = MagicMock(steps=200)
        connection.apply_decay(mock_npc)
        self.assertEqual(connection.strength, 94)

    def test_get_state(self):
        connection = Connection(
            relationship_type="friend",
            strength=75,
            steps=100,
            decay_rate=0.02,
            decay_threshold=1000,
        )
        state = connection.get_state()
        self.assertEqual(
            state,
            {
                "relationship_type": "friend",
                "strength": 75,
                "steps": 100,
                "decay_rate": 0.02,
                "decay_threshold": 1000,
            },
        )


class TestRelationships(unittest.TestCase):
    def setUp(self):
        self.relationships = Relationships()

    def test_add_connection(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        connection = self.relationships.get_connection("npc1")
        self.assertIsNotNone(connection)
        self.assertEqual(connection.relationship_type, "friend")

    def test_remove_connection(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        self.relationships.remove_connection("npc1")
        connection = self.relationships.get_connection("npc1")
        self.assertIsNone(connection)

    def test_update_connection_strength(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        self.relationships.update_connection_strength("npc1", 90)
        connection = self.relationships.get_connection("npc1")
        self.assertEqual(connection.strength, 90)

    def test_get_connection(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        connection = self.relationships.get_connection("npc1")
        self.assertIsNotNone(connection)
        self.assertEqual(connection.relationship_type, "friend")

    def test_get_all_connections(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        self.relationships.add_connection("npc2", "enemy", 25, 50, 0.01, 500)
        connections = self.relationships.get_all_connections()
        self.assertEqual(len(connections), 2)
        self.assertIn("npc1", connections)
        self.assertIn("npc2", connections)

    def test_update_connection_decay_rate(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        self.relationships.update_connection_decay_rate("npc1", 0.05)
        connection = self.relationships.get_connection("npc1")
        self.assertEqual(connection.decay_rate, 0.05)

    def test_update_connection_decay_threshold(self):
        self.relationships.add_connection(
            "npc1", "friend", 75, 100, 0.02, 1000
        )
        self.relationships.update_connection_decay_threshold("npc1", 1500)
        connection = self.relationships.get_connection("npc1")
        self.assertEqual(connection.decay_threshold, 1500)


class TestEncodingDecoding(unittest.TestCase):
    def test_encode_relationships(self):
        relationships = Relationships()
        relationships.add_connection("npc1", "friend", 75, 100, 0.02, 1000)
        encoded_data = encode_relationships(relationships)
        self.assertIsInstance(encoded_data, dict)
        self.assertIn("npc1", encoded_data)
        self.assertEqual(encoded_data["npc1"]["relationship_type"], "friend")

    def test_decode_relationships(self):
        json_data = {
            "npc1": {
                "relationship_type": "friend",
                "strength": 75,
                "steps": 100,
                "decay_rate": 0.02,
                "decay_threshold": 1000,
            }
        }
        relationships = decode_relationships(json_data)
        connection = relationships.get_connection("npc1")
        self.assertIsNotNone(connection)
        self.assertEqual(connection.relationship_type, "friend")

    def test_decode_empty_relationships(self):
        json_data: Mapping[str, Any] = {}
        relationships = decode_relationships(json_data)
        self.assertIsInstance(relationships, Relationships)
        self.assertEqual(len(relationships.get_all_connections()), 0)
