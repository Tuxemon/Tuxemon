# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tuxemon.trade_manager import TradeManager, TradeRecord, TradeResult


@pytest.fixture
def npc_manager():
    npc = MagicMock()
    owners = {}

    def get_owner(monster):
        if hasattr(monster, "_owner"):
            return monster._owner
        return owners.get(monster.instance_id)

    npc.get_monster_owner.side_effect = get_owner
    npc.get_monster_by_iid.side_effect = lambda iid: None

    return npc


@pytest.fixture
def manager(npc_manager):
    return TradeManager(npc_manager)


class MockPlayer:
    def __init__(self, name):
        self.name = name
        self.instance_id = uuid4()
        self.party = MagicMock()
        self.tuxepedia = MagicMock()


class MockMonster:
    def __init__(self, name, slug, owner):
        self.name = name
        self.slug = slug
        self.instance_id = uuid4()
        self.level = 5
        self._owner = owner

    def get_owner(self):
        return self._owner

    def set_owner(self, new_owner):
        self._owner = new_owner

    def set_acquisition(self, acquisition):
        self.acquisition = acquisition


@pytest.fixture
def players_and_monsters():
    player_a = MockPlayer("Better")
    player_b = MockPlayer("Call")
    monster_a = MockMonster("Flamey", "flamey_slug", player_a)
    monster_b = MockMonster("Splashy", "splashy_slug", player_b)
    player_a.party.monsters = [monster_a]
    player_b.party.monsters = [monster_b]
    return player_a, player_b, monster_a, monster_b


def test_execute_trade_success(manager, players_and_monsters):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    result = manager.execute_trade(monster_a, monster_b)
    assert result == TradeResult.SUCCESS
    assert len(manager.global_trade_log) == 2


def test_execute_trade_same_owner(manager, players_and_monsters):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    monster_b._owner = player_a
    result = manager.execute_trade(monster_a, monster_b)
    assert result == TradeResult.SAME_OWNER


def test_execute_trade_monster_not_found(manager, players_and_monsters):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    player_a.party.monsters = []
    result = manager.execute_trade(monster_a, monster_b)
    assert result == TradeResult.NOT_FOUND


@pytest.fixture
def sample_record(players_and_monsters):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    return TradeRecord(
        from_player="Better",
        to_player="Call",
        from_player_id=player_a.instance_id,
        to_player_id=player_b.instance_id,
        monster_given="flamey_slug",
        monster_received="splashy_slug",
        monster_given_id=monster_a.instance_id,
        monster_received_id=monster_b.instance_id,
        timestamp=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize(
    "query, expected",
    [
        pytest.param("Better", True, id="match_better"),
        pytest.param("Call", True, id="match_call"),
        pytest.param("Saul", False, id="no_match_saul"),
    ],
)
def test_was_traded_with_player(manager, sample_record, query, expected):
    manager.global_trade_log.append(sample_record)
    assert manager.was_traded_with_player(query) is expected


@pytest.mark.parametrize(
    "slug, expected",
    [
        pytest.param("flamey_slug", True, id="match_flamey"),
        pytest.param("splashy_slug", True, id="match_splashy"),
        pytest.param("leafy_slug", False, id="no_match_leafy"),
    ],
)
def test_was_traded_for_monster(manager, sample_record, slug, expected):
    manager.global_trade_log.append(sample_record)
    assert manager.was_traded_for_monster(slug) is expected


def test_get_trade_history(manager, sample_record):
    manager.global_trade_log.append(sample_record)
    lineage = manager.get_trade_history()
    assert len(lineage) == 1
    assert "Better traded flamey_slug for splashy_slug" in lineage[0]


def test_save_and_load_log(manager, npc_manager, sample_record):
    manager.global_trade_log.append(sample_record)
    saved = manager.save_log()
    new_manager = TradeManager(npc_manager)
    new_manager.event_bus = MagicMock()
    new_manager.load_log(saved)
    assert len(new_manager.global_trade_log) == 1
    assert new_manager.global_trade_log[0].from_player == "Better"


def test_accept_trade_expired_offer(
    manager, npc_manager, players_and_monsters
):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    all_monsters = [monster_a, monster_b]
    npc_manager.get_monster_by_iid.side_effect = lambda iid: next(
        (m for m in all_monsters if m.instance_id == iid), None
    )
    manager.propose_trade(monster_a, monster_b)
    offer = manager.pending_offers[0]
    offer.expires_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    result = manager.accept_trade(offer.offer_id)
    assert result == TradeResult.EXPIRED
    assert offer not in manager.pending_offers


def test_accept_trade_missing_monster(
    manager, npc_manager, players_and_monsters
):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    all_monsters = [monster_a, monster_b]
    npc_manager.get_monster_by_iid.side_effect = lambda iid: next(
        (m for m in all_monsters if m.instance_id == iid), None
    )
    manager.propose_trade(monster_a, monster_b)
    offer = manager.pending_offers[0]
    player_a.party.monsters = []
    player_b.party.monsters = []
    result = manager.accept_trade(offer.offer_id)
    assert result == TradeResult.NOT_FOUND


def test_accept_trade_nonexistent_offer(manager):
    fake_id = uuid4()
    result = manager.accept_trade(fake_id)
    assert result == TradeResult.NOT_FOUND


def test_get_trade_history_filtered(manager, sample_record):
    manager.global_trade_log.append(sample_record)
    lineage = manager.get_trade_history(player_name="Better")

    assert len(lineage) == 1
    assert "Better traded flamey_slug" in lineage[0]


def test_execute_trade_updates_party_and_ownership(
    manager, players_and_monsters
):
    player_a, player_b, monster_a, monster_b = players_and_monsters

    player_a.party.remove_monster = MagicMock()
    player_b.party.remove_monster = MagicMock()
    player_a.party.insert_monster_to_party = MagicMock()
    player_b.party.insert_monster_to_party = MagicMock()
    result = manager.execute_trade(monster_a, monster_b)
    assert result == TradeResult.SUCCESS

    player_a.party.remove_monster.assert_called_once_with(monster_a)
    player_b.party.remove_monster.assert_called_once_with(monster_b)
    player_a.party.insert_monster_to_party.assert_called_once()
    player_b.party.insert_monster_to_party.assert_called_once()


def test_execute_trade_updates_tuxepedia(manager, players_and_monsters):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    manager.execute_trade(monster_a, monster_b)
    player_a.tuxepedia.register_caught.assert_called_once_with(monster_b.slug)
    player_b.tuxepedia.register_caught.assert_called_once_with(monster_a.slug)


def test_execute_trade_publishes_event(manager, players_and_monsters):
    manager.event_bus = MagicMock()
    player_a, player_b, monster_a, monster_b = players_and_monsters
    manager.execute_trade(monster_a, monster_b)
    manager.event_bus.publish.assert_called_once()
    event_name, payload = manager.event_bus.publish.call_args[0]
    assert event_name == "trade_completed"
    assert len(payload) == 2


def test_accept_trade_invalid_ownership_change(
    manager, npc_manager, players_and_monsters
):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    all_monsters = [monster_a, monster_b]
    npc_manager.get_monster_by_iid.side_effect = lambda iid: next(
        (m for m in all_monsters if m.instance_id == iid), None
    )
    manager.propose_trade(monster_a, monster_b)
    offer = manager.pending_offers[0]
    monster_a.set_owner(player_b)
    result = manager.accept_trade(offer.offer_id)
    assert result == TradeResult.NOT_FOUND


def test_execute_scripted_trade_success(
    manager, npc_manager, players_and_monsters, monkeypatch
):
    player_a, player_b, monster_a, monster_b = players_and_monsters

    # Scripted trade creates a new monster via Monster.spawn_base
    class FakeNewMonster(MockMonster):
        def __init__(self):
            super().__init__("NewMon", "new_slug", player_a)

    fake_mon = FakeNewMonster()
    monkeypatch.setattr(
        "tuxemon.trade_manager.Monster.spawn_base",
        lambda slug, level: fake_mon,
    )
    player_a.party.replace_monster = MagicMock(return_value=True)
    result = manager.execute_scripted_trade(monster_a, "new_slug")
    assert result == TradeResult.SUCCESS
    player_a.party.replace_monster.assert_called_once_with(monster_a, fake_mon)
    assert fake_mon.acquisition is not None
    player_a.tuxepedia.register_caught.assert_called_once_with("new_slug")
    assert len(manager.global_trade_log) == 1
    record = manager.global_trade_log[0]
    assert record.monster_given == monster_a.slug
    assert record.monster_received == "new_slug"


def test_execute_scripted_trade_missing_player(
    manager, npc_manager, players_and_monsters
):
    player_a, player_b, monster_a, monster_b = players_and_monsters
    npc_manager.get_monster_owner.side_effect = lambda m: None
    result = manager.execute_scripted_trade(monster_a, "new_slug")
    assert result == TradeResult.NOT_FOUND
    assert manager.global_trade_log == []


def test_execute_scripted_trade_replace_failure(
    manager, npc_manager, players_and_monsters, monkeypatch
):
    player_a, player_b, monster_a, monster_b = players_and_monsters

    class FakeNewMonster(MockMonster):
        def __init__(self):
            super().__init__("NewMon", "new_slug", player_a)

    fake_mon = FakeNewMonster()
    monkeypatch.setattr(
        "tuxemon.trade_manager.Monster.spawn_base",
        lambda slug, level: fake_mon,
    )
    player_a.party.replace_monster = MagicMock(return_value=False)
    result = manager.execute_scripted_trade(monster_a, "new_slug")
    assert result == TradeResult.NOT_FOUND
    assert manager.global_trade_log == []
