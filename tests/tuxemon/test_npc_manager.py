# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tuxemon.npc_manager import NPCManager


@pytest.fixture
def npc_manager():
    return NPCManager()


@pytest.fixture
def session():
    s = MagicMock()
    s.player.slug = "player_slug"
    s.client.get_map_name.return_value = "map_a"
    return s


@pytest.fixture
def persistent_npcs(session):
    npc1 = MagicMock(
        slug="npc_1", instance_id=uuid4(), persistence=True, session=session
    )
    npc1.get_state.return_value = MagicMock(
        player_slug="npc_1", player_name="NPC One", current_map="map_a"
    )
    npc2 = MagicMock(
        slug="npc_2", instance_id=uuid4(), persistence=True, session=session
    )
    npc2.get_state.return_value = MagicMock(
        player_slug="npc_2", player_name="NPC Two", current_map="map_b"
    )
    return npc1, npc2


@pytest.mark.parametrize(
    "map_name, expected_location",
    [
        pytest.param("map_a", "npcs", id="npc_on_current_map"),
        pytest.param("map_b", "npcs_off_map", id="npc_off_current_map"),
    ],
)
@patch("tuxemon.npc_manager.NPC.from_save")
def test_load_persistent_npc_states(
    MockNPC, npc_manager, session, map_name, expected_location
):
    fake_npc = MagicMock(slug=f"npc_{expected_location}")
    MockNPC.return_value = fake_npc

    state = MagicMock(
        player_slug=f"npc_{expected_location}",
        player_name="NPC Test",
        current_map=map_name,
    )

    npc_manager.load_persistent_npc_states(session, [state])

    assert f"npc_{expected_location}" in getattr(
        npc_manager, expected_location
    )


def test_load_persistent_npc_states_skips_none_slug(npc_manager, session):
    state = MagicMock(
        player_slug=None, player_name="Nameless NPC", current_map="map_a"
    )
    npc_manager.load_persistent_npc_states(session, [state])
    assert npc_manager.npcs == {}
    assert npc_manager.npcs_off_map == {}


@patch("tuxemon.npc_manager.NPC.from_save")
def test_persistence_round_trip(
    MockNPC, npc_manager, session, persistent_npcs
):
    npc1, npc2 = persistent_npcs
    fake_npc1 = MagicMock(slug="npc_1")
    fake_npc2 = MagicMock(slug="npc_2")
    MockNPC.side_effect = [fake_npc1, fake_npc2]
    npc_manager.add_npc(npc1)
    npc_manager.add_npc_off_map(npc2)
    states = npc_manager.get_persistent_npc_states(session)
    assert len(states) == 2
    npc_manager.npcs.clear()
    npc_manager.npcs_off_map.clear()
    npc_manager.load_persistent_npc_states(session, states)
    assert "npc_1" in npc_manager.npcs
    assert "npc_2" in npc_manager.npcs_off_map
    assert "npc_1" not in npc_manager.npcs_off_map
    assert "npc_2" not in npc_manager.npcs


@patch("tuxemon.npc_manager.NPC.from_save")
def test_load_persistent_overwrites_duplicate_slugs(
    MockNPC, npc_manager, session
):
    state1 = MagicMock(player_slug="npc_x", current_map="map_a")
    state2 = MagicMock(player_slug="npc_x", current_map="map_b")
    npc_a = MagicMock(slug="npc_x")
    npc_b = MagicMock(slug="npc_x")
    MockNPC.side_effect = [npc_a, npc_b]
    npc_manager.load_persistent_npc_states(session, [state1, state2])
    assert "npc_x" in npc_manager.npcs_off_map
    assert "npc_x" not in npc_manager.npcs


def test_get_persistent_npc_states_skips_missing_session(
    npc_manager, session, caplog
):
    npc = MagicMock(slug="npc_1", persistence=True, session=None)
    npc_manager.add_npc(npc)

    with caplog.at_level(logging.WARNING):
        states = npc_manager.get_persistent_npc_states(session)

    assert states == []
    assert "missing session" in caplog.text


def test_get_persistent_npc_states_ignores_non_persistent(
    npc_manager, session
):
    npc = MagicMock(slug="npc_np", persistence=False, session=session)
    npc_manager.add_npc(npc)
    states = npc_manager.get_persistent_npc_states(session)
    assert states == []


@patch("tuxemon.npc_manager.NPC.from_save")
def test_load_persistent_mixed_valid_invalid(MockNPC, npc_manager, session):
    valid = MagicMock(player_slug="npc_ok", current_map="map_a")
    invalid = MagicMock(player_slug=None, current_map="map_a")
    fake_npc = MagicMock(slug="npc_ok")
    MockNPC.return_value = fake_npc
    npc_manager.load_persistent_npc_states(session, [valid, invalid])
    assert "npc_ok" in npc_manager.npcs
    assert npc_manager.npcs_off_map == {}


def test_clear_npcs_filters_correctly(npc_manager):
    persistent = MagicMock(slug="p", persistence=True)
    non_persistent = MagicMock(slug="np", persistence=False)
    npc_manager.add_npc(persistent)
    npc_manager.add_npc(non_persistent)
    npc_manager.clear_npcs()
    assert "p" in npc_manager.npcs
    assert "np" not in npc_manager.npcs
    non_persistent.remove_collision.assert_called_once()


def test_add_clients_to_map_missing_map_name(npc_manager):
    registry = {"c1": {"sprite": MagicMock(slug="npc1")}}
    npc_manager.add_clients_to_map(registry, "map_a")
    assert "npc1" in npc_manager.npcs_off_map


def test_add_clients_to_map_moves_between_maps(npc_manager):
    sprite = MagicMock(slug="npc1")
    registry = {"c1": {"sprite": sprite, "map_name": "map_a"}}
    npc_manager.add_clients_to_map(registry, "map_a")
    assert "npc1" in npc_manager.npcs
    registry["c1"]["map_name"] = "map_b"
    npc_manager.add_clients_to_map(registry, "map_a")
    assert "npc1" in npc_manager.npcs_off_map
    assert "npc1" not in npc_manager.npcs


def test_public_dict_reflects_internal_state(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc(npc)
    assert "npc1" in npc_manager._on_map._data
    assert npc_manager.npcs["npc1"] is npc


def test_move_npc_between_maps(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc(npc)
    npc_manager.add_npc_off_map(npc)
    assert "npc1" not in npc_manager.npcs
    assert "npc1" in npc_manager.npcs_off_map
    assert npc_manager.npcs_off_map["npc1"] is npc


def test_clear_npcs_preserves_persistent_on_and_off_map(npc_manager):
    p1 = MagicMock(slug="p1", persistence=True)
    p2 = MagicMock(slug="p2", persistence=True)
    np = MagicMock(slug="np", persistence=False)
    npc_manager.add_npc(p1)
    npc_manager.add_npc_off_map(p2)
    npc_manager.add_npc(np)
    npc_manager.clear_npcs()
    assert "p1" in npc_manager.npcs
    assert "p2" in npc_manager.npcs_off_map
    assert "np" not in npc_manager.npcs


def test_get_entity_pos_only_checks_on_map(npc_manager):
    npc_on = MagicMock(slug="on", tile_pos=(1, 1))
    npc_off = MagicMock(slug="off", tile_pos=(1, 1))
    npc_manager.add_npc(npc_on)
    npc_manager.add_npc_off_map(npc_off)
    assert npc_manager.get_entity_pos((1, 1)) is npc_on


@patch("tuxemon.npc_manager.NPC.from_save")
def test_load_persistent_does_not_clear_existing(
    MockNPC, npc_manager, session
):
    existing = MagicMock(slug="existing")
    npc_manager.add_npc(existing)
    state = MagicMock(player_slug="npc_new", current_map="map_a")
    new_npc = MagicMock(slug="npc_new")
    MockNPC.return_value = new_npc
    npc_manager.load_persistent_npc_states(session, [state])
    assert "existing" in npc_manager.npcs
    assert "npc_new" in npc_manager.npcs


def test_update_npcs_only_updates_on_map(npc_manager):
    client = MagicMock()
    npc_on = MagicMock(slug="on", update_location=False)
    npc_off = MagicMock(slug="off", update_location=False)
    npc_manager.add_npc(npc_on)
    npc_manager.add_npc_off_map(npc_off)
    npc_manager.update_npcs(0.1, client)
    npc_on.update.assert_called_once()
    npc_off.update.assert_not_called()


def test_add_clients_to_map_ignores_entries_without_sprite(npc_manager):
    registry = {
        "c1": {"map_name": "map_a"},
        "c2": {"sprite": MagicMock(slug="npc1"), "map_name": "map_a"},
    }
    npc_manager.add_clients_to_map(registry, "map_a")
    assert "npc1" in npc_manager.npcs
    assert len(npc_manager.npcs) == 1


def test_public_dicts_are_copies(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc(npc)

    npc_manager.npcs.pop("npc1")
    assert "npc1" in npc_manager._on_map._data


def test_get_npc_returns_correct(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc(npc)
    assert npc_manager.get_npc("npc1") is npc


def test_get_npc_returns_none(npc_manager):
    assert npc_manager.get_npc("missing") is None


def test_get_npc_off_map_returns_correct(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc_off_map(npc)
    assert npc_manager.get_npc_off_map("npc1") is npc


def test_get_npc_off_map_returns_none(npc_manager):
    assert npc_manager.get_npc_off_map("missing") is None


def test_get_npc_off_map_by_iid(npc_manager):
    npc = MagicMock(slug="npc1", instance_id=uuid4())
    npc_manager.add_npc_off_map(npc)
    assert npc_manager.get_npc_off_map_by_iid(npc.instance_id) is npc


def test_get_npc_off_map_by_iid_none(npc_manager):
    assert npc_manager.get_npc_off_map_by_iid(uuid4()) is None


def test_get_all_entities(npc_manager):
    npc1 = MagicMock(slug="npc1")
    npc2 = MagicMock(slug="npc2")
    npc_manager.add_npc(npc1)
    npc_manager.add_npc(npc2)
    assert set(npc_manager.get_all_entities()) == {npc1, npc2}


def test_get_all_monsters(npc_manager):
    m1 = MagicMock()
    m2 = MagicMock()
    npc = MagicMock(slug="npc1", monsters=[m1, m2])
    npc_manager.add_npc(npc)
    assert npc_manager.get_all_monsters() == [m1, m2]


def test_get_all_monsters_empty(npc_manager):
    npc = MagicMock(slug="npc1", monsters=[])
    npc_manager.add_npc(npc)
    assert npc_manager.get_all_monsters() == []


def test_get_monster_owner_on_map(npc_manager):
    monster = MagicMock()
    npc = MagicMock(slug="npc1", monsters=[monster])
    npc_manager.add_npc(npc)
    assert npc_manager.get_monster_owner(monster) is npc


def test_get_monster_owner_off_map(npc_manager):
    monster = MagicMock()
    npc = MagicMock(slug="npc1", monsters=[monster])
    npc_manager.add_npc_off_map(npc)
    assert npc_manager.get_monster_owner(monster) is npc


def test_get_monster_owner_none(npc_manager):
    monster = MagicMock()
    assert npc_manager.get_monster_owner(monster) is None


def test_get_monster_by_iid(npc_manager):
    monster = MagicMock(instance_id=uuid4())
    npc = MagicMock(slug="npc1", monsters=[monster])
    npc_manager.add_npc(npc)
    assert npc_manager.get_monster_by_iid(monster.instance_id) is monster


def test_get_monster_by_iid_none(npc_manager):
    assert npc_manager.get_monster_by_iid(uuid4()) is None


def test_remove_npc(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc(npc)
    npc_manager.remove_npc("npc1")
    assert "npc1" not in npc_manager.npcs


def test_remove_npc_off_map(npc_manager):
    npc = MagicMock(slug="npc1")
    npc_manager.add_npc_off_map(npc)
    npc_manager.remove_npc_off_map("npc1")
    assert "npc1" not in npc_manager.npcs_off_map


def test_get_all_slugs(npc_manager):
    npc1 = MagicMock(slug="npc1")
    npc2 = MagicMock(slug="npc2")
    npc_manager.add_npc(npc1)
    npc_manager.add_npc_off_map(npc2)
    assert set(npc_manager.get_all_slugs()) == {"npc1", "npc2"}


def test_handle_player_teleport_updates_client_and_npcs(npc_manager):
    client = MagicMock()
    client.event_data = {}
    client.get_map_name.return_value = "map_a"
    network = MagicMock()
    network.is_connected.return_value = True
    network.client.registry = {}
    network.client.update_player = MagicMock()
    char = MagicMock(facing=MagicMock(value="north"))
    npc_manager.handle_player_teleport(client, char, network)
    assert client.event_data["transition"] is False
    network.client.update_player.assert_called_once()


def test_handle_player_teleport_no_network(npc_manager):
    client = MagicMock()
    client.event_data = {}
    client.get_map_name.return_value = "map_a"
    network = MagicMock()
    network.is_connected.return_value = False
    char = MagicMock()
    npc_manager.handle_player_teleport(client, char, network)
    assert client.event_data["transition"] is False
