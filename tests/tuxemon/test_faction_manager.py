# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock

import pytest

from tuxemon.db import FactionAlignment, FactionRelationStatus
from tuxemon.event.eventbus import EventBus
from tuxemon.faction.faction import Faction
from tuxemon.faction.manager import FactionManager


@pytest.fixture
def faction_manager():
    return FactionManager(EventBus())


@pytest.fixture
def faction():
    return Faction()


def test_init(faction_manager):
    assert faction_manager._factions == {}
    assert faction_manager._membership_cache == {}


def test_load_core_factions(faction_manager, mocker):
    mock_load = mocker.patch.object(Faction, "load_from_db")
    mock_register = mocker.patch.object(faction_manager, "register")

    faction_manager.load_core_factions(["f1", "f2"])

    assert mock_load.call_count == 2
    assert mock_register.call_count == 2


def test_register(faction_manager, faction):
    faction.slug = "faction1"
    faction_manager.register(faction)
    assert "faction1" in faction_manager._factions


def test_get(faction_manager, faction):
    faction.slug = "faction1"
    faction_manager.register(faction)
    assert faction_manager.get("faction1") is faction


def test_all_factions(faction_manager):
    f1, f2 = Faction(), Faction()
    f1.slug, f2.slug = "f1", "f2"
    faction_manager.register(f1)
    faction_manager.register(f2)
    assert len(faction_manager.all_factions()) == 2


def test_is_loaded(faction_manager, faction):
    faction.slug = "faction1"
    faction_manager.register(faction)
    assert faction_manager.is_loaded("faction1")


def test_get_factions_by_member(faction_manager):
    f1, f2 = Faction(), Faction()
    f1.slug, f2.slug = "f1", "f2"
    f1.add_member("npc1")
    faction_manager.register(f1)
    faction_manager.register(f2)

    assert len(faction_manager.get_factions_by_member("npc1")) == 1


def test_clear_membership_cache(faction_manager):
    f1 = Faction()
    f1.slug = "f1"
    f1.add_member("npc1")
    faction_manager.register(f1)

    faction_manager.get_factions_by_member("npc1")
    faction_manager.clear_membership_cache("npc1")

    assert "npc1" not in faction_manager._membership_cache


def test_resolve_diplomacy_allies(faction_manager):
    f1, f2 = Faction(), Faction()
    f1.slug, f2.slug = "f1", "f2"
    f1.alignment = FactionAlignment.LAWFUL
    f2.alignment = FactionAlignment.LAWFUL

    faction_manager.register(f1)
    faction_manager.register(f2)

    faction_manager.resolve_diplomacy("f1", "f2")
    assert f1.get_relation("f2") == FactionRelationStatus.ALLY


def test_find_factions_by_alignment(faction_manager):
    f1, f2 = Faction(), Faction()
    f1.slug, f2.slug = "f1", "f2"
    f1.alignment = FactionAlignment.LAWFUL
    f2.alignment = FactionAlignment.CHAOTIC

    faction_manager.register(f1)
    faction_manager.register(f2)

    lawful = faction_manager.find_factions_by_alignment(
        FactionAlignment.LAWFUL
    )
    assert len(lawful) == 1


def test_rank_npc_globally(faction_manager):
    f1 = Faction()
    f1.slug = "f1"
    f1.add_member("npc1")
    faction_manager.register(f1)

    assert faction_manager.rank_npc_globally("npc1") is not None


def test_get_state(faction_manager):
    save_data = {
        "factions_manager": {
            "f1": {
                "members": {"npc1": {"reputation": 10, "is_member": True}},
                "public_reputation": 5,
                "relations": {"f2": "ALLY"},
            }
        }
    }

    f1 = Faction()
    f1.slug = "f1"
    faction_manager.register(f1)

    faction_manager.get_state(save_data)

    assert f1.get_reputation("npc1") == 10
    assert "npc1" in f1.members
    assert f1.public_reputation == 5
    assert f1.get_relation("f2") == FactionRelationStatus.ALLY


def test_set_state(faction_manager):
    npc_manager = Mock()
    npc_manager.get_all_slugs.return_value = ["npc1"]

    f1 = Faction()
    f1.slug = "f1"
    f1.add_member("npc1")
    f1.reputation["npc1"] = 10
    f1.set_public_reputation(5)
    f1.set_relation("f2", FactionRelationStatus.ALLY)

    faction_manager.register(f1)

    state = faction_manager.set_state(npc_manager)

    assert "factions_manager" in state
    fdata = state["factions_manager"]["f1"]

    assert fdata["members"]["npc1"]["reputation"] == 10
    assert fdata["members"]["npc1"]["is_member"]
    assert fdata["public_reputation"] == 5
    assert fdata["relations"]["f2"] == "ALLY"


def test_load_core_factions_empty_list(faction_manager):
    faction_manager.load_core_factions([])
    assert faction_manager.all_factions() == []


def test_register_duplicate_faction(faction_manager):
    f1 = Faction()
    f1.slug = "f1"
    faction_manager.register(f1)
    faction_manager.register(f1)
    assert len(faction_manager.all_factions()) == 1


def test_get_non_existent_faction(faction_manager):
    assert faction_manager.get("missing") is None


def test_all_factions_empty(faction_manager):
    assert faction_manager.all_factions() == []


def test_is_loaded_non_existent(faction_manager):
    assert not faction_manager.is_loaded("missing")


def test_get_factions_by_member_empty(faction_manager):
    assert faction_manager.get_factions_by_member("npc1") == []


def test_clear_membership_cache_all(faction_manager):
    f1 = Faction()
    f1.slug = "f1"
    f1.add_member("npc1")
    faction_manager.register(f1)

    faction_manager.get_factions_by_member("npc1")
    faction_manager.clear_membership_cache()

    assert faction_manager._membership_cache == {}


def test_update_triggers_maintenance(faction_manager):
    f = Faction()
    f.slug = "f1"
    f.add_member("npc1")
    f.update = Mock()
    f.evaluate_rank_change = Mock()

    faction_manager.register(f)

    session = Mock()
    session.player = Mock()
    session.player.variable_manager = Mock()
    session.player.variable_manager.get_state.return_value = {}

    faction_manager.update(601.0, session)

    f.update.assert_called_once_with(601.0)
    f.evaluate_rank_change.assert_called_with(
        "npc1", session.player.variable_manager
    )


def test_resolve_diplomacy_rivals(faction_manager):
    f1, f2 = Faction(), Faction()
    f1.slug, f2.slug = "f1", "f2"
    f1.alignment = FactionAlignment.LAWFUL
    f2.alignment = FactionAlignment.CHAOTIC

    faction_manager.register(f1)
    faction_manager.register(f2)

    faction_manager.resolve_diplomacy("f1", "f2")
    assert f1.get_relation("f2") == FactionRelationStatus.RIVAL


def test_get_factions_by_member_cache_reuse(faction_manager, mocker):
    f = Faction()
    f.slug = "f1"
    f.add_member("npc1")
    faction_manager.register(f)
    result1 = faction_manager.get_factions_by_member("npc1")
    mock_has = mocker.patch.object(Faction, "has_member", return_value=False)
    result2 = faction_manager.get_factions_by_member("npc1")
    mock_has.assert_not_called()
    assert result1 == result2


def test_on_faction_loaded_logs(faction_manager, caplog):
    f = Faction()
    f.slug = "f1"

    with caplog.at_level("INFO", logger="tuxemon.faction.manager"):
        faction_manager.on_faction_loaded(f)

    assert any("detected faction loaded" in msg for msg in caplog.messages)


def test_load_core_factions_failure(faction_manager, mocker):
    mocker.patch.object(
        Faction, "load_from_db", side_effect=Exception("DB error")
    )
    faction_manager.load_core_factions(["bad"])
    assert faction_manager.all_factions() == []
