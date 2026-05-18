# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Mapping
from typing import Any

import pytest

from tuxemon.event.eventbus import EventBus
from tuxemon.relationship import (
    Connection,
    RelationshipConstants,
    Relationships,
    RelationshipStatus,
    decode_relationships,
    encode_relationships,
)


@pytest.mark.parametrize(
    "kwargs, expected_state",
    [
        pytest.param(
            {
                "relationship_type": "friend",
                "strength": 75,
                "steps": 100,
                "decay_rate": 0.02,
                "decay_threshold": 1000,
            },
            {
                "relationship_type": "friend",
                "strength": 75,
                "steps": 100,
                "decay_rate": 0.02,
                "decay_threshold": 1000,
            },
            id="friend_init",
        ),
        pytest.param(
            {
                "relationship_type": "rival",
                "strength": 50,
                "steps": 10,
                "decay_rate": 0.1,
                "decay_threshold": 200,
            },
            {
                "relationship_type": "rival",
                "strength": 50,
                "steps": 10,
                "decay_rate": 0.1,
                "decay_threshold": 200,
            },
            id="rival_init",
        ),
    ],
)
def test_connection_initialization(kwargs, expected_state):
    connection = Connection(**kwargs)
    assert connection.get_state() == expected_state


def test_update_steps():
    connection = Connection(relationship_type="friend")
    connection.update_steps(current_steps=200)
    assert connection.steps == 200


def test_apply_decay_no_decay():
    connection = Connection(
        relationship_type="friend",
        strength=75,
        steps=100,
        decay_threshold=500,
    )
    connection.apply_decay(current_steps=400)
    assert connection.strength == 75


@pytest.mark.parametrize(
    "strength, expected",
    [
        pytest.param(5, 4, id="min_strength"),
        pytest.param(95, 94, id="max_strength"),
    ],
)
def test_apply_decay_strength_variants(strength, expected):
    connection = Connection(
        relationship_type="friend",
        strength=strength,
        steps=0,
        decay_rate=0.5,
        decay_threshold=100,
    )
    connection.apply_decay(current_steps=200)
    assert connection.strength == expected


def test_get_state():
    connection = Connection(
        relationship_type="friend",
        strength=75,
        steps=100,
        decay_rate=0.02,
        decay_threshold=1000,
    )
    state = connection.get_state()
    assert state == {
        "relationship_type": "friend",
        "strength": 75,
        "steps": 100,
        "decay_rate": 0.02,
        "decay_threshold": 1000,
    }


def test_apply_decay_with_profile_mod():
    connection = Connection(
        "friend", strength=50, steps=0, decay_rate=1.0, decay_threshold=100
    )
    connection.get_profile_value = lambda key: (
        2.0 if key == "decay_rate_mod" else 1.0
    )
    connection.apply_decay(current_steps=200)
    assert connection.strength == 46


def test_get_status():
    connection = Connection("friend", strength=90)
    status = connection.get_status()
    assert status == RelationshipStatus.BEST_FRIEND


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def relationships(event_bus):
    return Relationships(event_bus)


@pytest.fixture
def connection():
    return Connection("friend", 75, 100, 0.02, 1000)


# Relationships tests
def test_add_connection(relationships, connection):
    relationships.add_connection("npc1", connection)
    conn = relationships.get_connection("npc1")
    assert conn is not None
    assert conn.relationship_type == "friend"


def test_remove_connection(relationships, connection):
    relationships.add_connection("npc1", connection)
    relationships.remove_connection("npc1")
    assert relationships.get_connection("npc1") is None


def test_update_connection_strength(relationships, connection):
    relationships.add_connection("npc1", connection)
    relationships.update_connection_strength("npc1", 90)
    assert relationships.get_connection("npc1").strength == 90


def test_get_connection(relationships, connection):
    relationships.add_connection("npc1", connection)
    conn = relationships.get_connection("npc1")
    assert conn is not None
    assert conn.relationship_type == "friend"


def test_get_all_connections(relationships, connection):
    relationships.add_connection("npc1", connection)
    other = Connection("enemy", 25, 50, 0.01, 500)
    relationships.add_connection("npc2", other)
    connections = relationships.get_all_connections()
    assert len(connections) == 2
    assert "npc1" in connections
    assert "npc2" in connections


def test_update_connection_decay_rate(relationships, connection):
    relationships.add_connection("npc1", connection)
    relationships.update_connection_decay_rate("npc1", 0.05)
    assert relationships.get_connection("npc1").decay_rate == 0.05


def test_update_connection_decay_threshold(relationships, connection):
    relationships.add_connection("npc1", connection)
    relationships.update_connection_decay_threshold("npc1", 1500)
    assert relationships.get_connection("npc1").decay_threshold == 1500


@pytest.mark.parametrize(
    "new_strength, expected",
    [
        pytest.param(
            999,
            RelationshipConstants.STRENGTH[1],
            id="clamp_max",
        ),
        pytest.param(
            -50,
            RelationshipConstants.STRENGTH[0],
            id="clamp_min",
        ),
    ],
)
def test_update_connection_strength_clamps(
    relationships, connection, new_strength, expected
):
    relationships.add_connection("npc1", connection)
    relationships.update_connection_strength("npc1", new_strength)
    assert relationships.get_connection("npc1").strength == expected


def test_modify_connection_strength_with_increase_mod(relationships):
    conn = Connection("friend", 50, 0, 0.01, 100)
    relationships.add_connection("npc1", conn)
    conn.get_profile_value = lambda key: (
        2.0 if key == "strength_increase_mod" else 1.0
    )
    relationships.modify_connection_strength("npc1", 10)
    assert conn.strength == 70


def test_modify_connection_strength_with_decrease_mod(relationships):
    conn = Connection("friend", 50, 0, 0.01, 100)
    relationships.add_connection("npc1", conn)
    conn.get_profile_value = lambda key: (
        2.0 if key == "strength_decrease_mod" else 1.0
    )
    relationships.modify_connection_strength("npc1", -10)
    assert conn.strength == 30


# Encoding/Decoding tests
def test_encode_relationships(relationships, connection):
    relationships.add_connection("npc1", connection)
    encoded = encode_relationships(relationships)
    assert isinstance(encoded, dict)
    assert "npc1" in encoded
    assert encoded["npc1"]["relationship_type"] == "friend"


def test_decode_relationships(event_bus):
    json_data = {
        "npc1": {
            "relationship_type": "friend",
            "strength": 75,
            "steps": 100,
            "decay_rate": 0.02,
            "decay_threshold": 1000,
        }
    }
    relationships = decode_relationships(json_data, event_bus)
    conn = relationships.get_connection("npc1")
    assert conn is not None
    assert conn.relationship_type == "friend"


def test_decode_empty_relationships(event_bus):
    json_data: Mapping[str, Any] = {}
    relationships = decode_relationships(json_data, event_bus)
    assert isinstance(relationships, Relationships)
    assert len(relationships.get_all_connections()) == 0


def test_encode_decode_roundtrip(relationships, connection, event_bus):
    relationships.add_connection("npc1", connection)
    encoded = encode_relationships(relationships)
    decoded = decode_relationships(encoded, event_bus)
    conn = decoded.get_connection("npc1")
    assert conn.relationship_type == "friend"
    assert conn.strength == 75
    assert conn.steps == 100


# EventBus integration tests
@pytest.fixture
def relationships_with_eventbus(event_bus):
    conn = Connection("friend", 50, 0, 0.01, 100)
    rel = Relationships(event_bus=event_bus)
    rel.add_connection("npc1", conn)
    return rel


def test_strength_update_via_eventbus(event_bus, relationships_with_eventbus):
    event_bus.publish(
        "relationship_modified",
        npc_slug="npc1",
        attribute="strength",
        value=80,
    )
    assert relationships_with_eventbus.get_connection("npc1").strength == 80


def test_decay_rate_update_via_eventbus(
    event_bus, relationships_with_eventbus
):
    event_bus.publish(
        "relationship_modified",
        npc_slug="npc1",
        attribute="decay_rate",
        value=0.05,
    )
    assert (
        relationships_with_eventbus.get_connection("npc1").decay_rate == 0.05
    )


def test_decay_threshold_update_via_eventbus(
    event_bus, relationships_with_eventbus
):
    event_bus.publish(
        "relationship_modified",
        npc_slug="npc1",
        attribute="decay_threshold",
        value=200,
    )
    assert (
        relationships_with_eventbus.get_connection("npc1").decay_threshold
        == 200
    )


def test_invalid_attribute_via_eventbus(
    event_bus, relationships_with_eventbus
):
    event_bus.publish(
        "relationship_modified",
        npc_slug="npc1",
        attribute="unknown_attr",
        value=123,
    )
    assert relationships_with_eventbus.get_connection("npc1").strength == 50
