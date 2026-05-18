# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import FactionRelationStatus, RankStep
from tuxemon.faction.faction import Faction
from tuxemon.game_variables import GameVariablesManager


@pytest.fixture
def faction():
    return Faction()


def test_init(faction, mocker):
    mocker.patch("tuxemon.locale.locale.T.translate", return_value="")
    assert faction.slug == ""
    assert faction.name == ""
    assert faction.description == ""
    assert faction.kind is None
    assert faction.alignment is None
    assert faction.badge_id is None
    assert faction.leader_char is None
    assert faction.ranks == []
    assert faction.members == []
    assert faction.reputation == {}
    assert faction.relations == {}


@pytest.mark.parametrize(
    "rep,expected",
    [
        pytest.param(50, None, id="below_first_rank"),
        pytest.param(150, "test_rank1", id="first_rank"),
        pytest.param(250, "test_rank2", id="second_rank"),
    ],
)
def test_get_rank_for_reputation(faction, rep, expected):
    faction.ranks = [
        RankStep(threshold=100, title="test_rank1"),
        RankStep(threshold=200, title="test_rank2"),
    ]
    assert faction.get_rank_for_reputation(rep) == expected


def test_get_current_rank(faction):
    faction.ranks = [
        RankStep(threshold=100, title="test_rank1"),
        RankStep(threshold=200, title="test_rank2"),
    ]
    faction.reputation = {"test_npc": 150}
    assert faction.get_current_rank("test_npc") == "test_rank1"


def test_get_relation(faction):
    faction.relations = {"test_faction": FactionRelationStatus.ALLY}
    assert faction.get_relation("test_faction") == FactionRelationStatus.ALLY
    assert (
        faction.get_relation("other_faction") == FactionRelationStatus.UNKNOWN
    )


def test_is_ally(faction):
    faction.relations = {"test_faction": FactionRelationStatus.ALLY}
    assert faction.is_ally("test_faction")
    assert not faction.is_ally("other_faction")


def test_set_relation(faction):
    faction.set_relation("test_faction", FactionRelationStatus.ALLY)
    assert faction.relations == {"test_faction": FactionRelationStatus.ALLY}


def test_modify_reputation(faction):
    faction.reputation = {"test_npc": 100}
    faction.modify_reputation("test_npc", 50)
    assert faction.reputation == {"test_npc": 150}


def test_get_reputation(faction):
    faction.reputation = {"test_npc": 100}
    assert faction.get_reputation("test_npc") == 100


def test_add_member(faction):
    faction.add_member("test_npc")
    assert faction.members == ["test_npc"]


def test_remove_member(faction):
    faction.members = ["test_npc"]
    faction.remove_member("test_npc")
    assert faction.members == []


def test_has_member(faction):
    faction.members = ["test_npc"]
    assert faction.has_member("test_npc")
    assert not faction.has_member("other_npc")


@pytest.mark.parametrize(
    "initial,new_rep,expected",
    [
        pytest.param("test_rank1", 250, "test_rank2", id="promotion_to_rank2"),
        pytest.param("test_rank2", 150, "test_rank1", id="demotion_to_rank1"),
        pytest.param("test_rank2", 50, None, id="demotion_to_none"),
    ],
)
def test_evaluate_rank_change(faction, initial, new_rep, expected):
    faction.ranks = [
        RankStep(threshold=100, title="test_rank1"),
        RankStep(threshold=200, title="test_rank2"),
    ]
    faction.reputation = {"test_npc": new_rep}
    faction._rank_cache = {"test_npc": initial}

    new_rank = faction.evaluate_rank_change("test_npc", MagicMock())
    assert new_rank == expected

    if expected is not None:
        assert faction.get_current_rank("test_npc") == expected
    else:
        assert faction.get_current_rank("test_npc") == initial


def test_can_be_promoted(faction):
    faction.ranks = [RankStep(threshold=100, title="test_rank")]
    faction.reputation = {"test_npc": 150}
    assert faction.can_be_promoted(
        "test_npc", GameVariablesManager(initial_player={})
    )


def test_update_decay_towards_baseline(faction):
    faction._public_reputation = 30
    faction._neutral_baseline = 50
    faction.update(10.0)
    assert faction._public_reputation > 30


def test_update_removes_member_below_threshold(faction):
    faction.ranks = [RankStep(threshold=100, title="Novice")]
    faction.add_member("npc1")
    faction.reputation["npc1"] = 10
    faction._decay_timer = 600.0
    faction.update(1.0)
    assert "npc1" not in faction.members


def test_power_level_calculation(faction):
    faction.add_member("npc1")
    faction.reputation["npc1"] = 20
    assert faction.power_level == 20 + 10


def test_power_level_empty(faction):
    assert faction.power_level == 0


def test_from_save_data_and_to_save_data_roundtrip(faction):
    data = {"npc1": {"reputation": 10, "is_member": True}}
    relations = {"faction2": "ALLY"}

    faction.from_save_data(data, public_reputation=5, relations=relations)
    save = faction.to_save_data(["npc1"])

    assert save["members"]["npc1"]["reputation"] == 10
    assert save["public_reputation"] == 5
    assert save["relations"]["faction2"] == "ALLY"


def test_to_save_data_returns_none_for_empty_faction(faction):
    assert faction.to_save_data(["npc1"]) is None


def test_set_relation_publishes_event(faction, mocker):
    mock_bus = mocker.Mock()
    faction._event_bus = mock_bus
    faction.set_relation("factionX", FactionRelationStatus.ALLY)
    mock_bus.publish.assert_called()


def test_add_member_publishes_event(faction, mocker):
    mock_bus = mocker.Mock()
    faction._event_bus = mock_bus
    faction.add_member("npc1")
    mock_bus.publish.assert_called()


def test_remove_member_publishes_event(faction, mocker):
    mock_bus = mocker.Mock()
    faction._event_bus = mock_bus
    faction.members = ["npc1"]
    faction.remove_member("npc1")
    mock_bus.publish.assert_called()


def test_rank_cache_invalidation_on_reputation_change(faction):
    faction._rank_cache["npc1"] = "OldRank"
    faction.modify_reputation("npc1", 5)
    assert "npc1" not in faction._rank_cache


def test_promotion_with_unsatisfied_requirements(faction):
    faction.ranks = [
        RankStep(
            threshold=100,
            title="Champion",
            requirement={"variables": [{"key": "badge", "value": "fire"}]},
        )
    ]
    faction.reputation["npc1"] = 150

    game_vars = GameVariablesManager(initial_player={"badge": "water"})
    assert not faction.can_be_promoted("npc1", game_vars)


def test_set_public_reputation_bounds(faction):
    faction.set_public_reputation(-10)
    assert faction.public_reputation == 0

    faction.set_public_reputation(999)
    assert faction.public_reputation == faction.MAX_PUBLIC_REPUTATION
