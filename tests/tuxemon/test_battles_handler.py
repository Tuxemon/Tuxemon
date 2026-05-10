# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import time

import pytest

from tuxemon.battle import Battle
from tuxemon.db import OutputBattle
from tuxemon.entity.battle import BattlesHandler
from tuxemon.save_system.save_state import NPCState


@pytest.fixture
def handler():
    return BattlesHandler("player")


def make_battle(fighter="player", opponent="npc", outcome=OutputBattle.WON):
    return Battle().from_save_data(
        {
            "fighter": fighter,
            "opponent": opponent,
            "outcome": outcome,
            "timestamp": time.time(),
        }
    )


def test_init(handler):
    assert handler.get_battles() == []


def test_add_battle(handler):
    handler.add_battle(make_battle())
    assert len(handler.get_battles()) == 1


def test_get_battles(handler):
    handler.add_battle(make_battle(outcome=OutputBattle.WON))
    handler.add_battle(make_battle(outcome=OutputBattle.LOST))
    assert len(handler.get_battles()) == 2


def test_clear_battles(handler):
    handler.add_battle(make_battle())
    handler.clear_battles()
    assert len(handler.get_battles()) == 0


def test_has_fought_and_outcome(handler):
    handler.add_battle(make_battle(outcome=OutputBattle.WON))
    assert handler.has_fought_and_outcome(OutputBattle.WON.value, "npc")


def test_get_last_battle_outcome(handler):
    handler.add_battle(make_battle(outcome=OutputBattle.WON))
    handler.add_battle(make_battle(outcome=OutputBattle.LOST))
    assert handler.get_last_battle_outcome("npc") == OutputBattle.LOST


def test_get_battle_outcome_stats(handler):
    handler.add_battle(make_battle(outcome=OutputBattle.WON))
    handler.add_battle(make_battle(outcome=OutputBattle.LOST))

    stats = handler.get_battle_outcome_stats()
    assert stats[OutputBattle.WON] == 1
    assert stats[OutputBattle.LOST] == 1
    assert stats[OutputBattle.DRAW] == 0


def test_get_battle_outcome_summary(handler):
    handler.add_battle(make_battle(outcome=OutputBattle.WON))
    handler.add_battle(make_battle(outcome=OutputBattle.LOST))

    summary = handler.get_battle_outcome_summary()
    assert summary["total"] == 2
    assert summary["won"] == 1
    assert summary["lost"] == 1
    assert summary["draw"] == 0


def test_record_battle(handler):
    before = time.time()
    battle = handler.record_battle("npc", OutputBattle.DRAW)
    after = time.time()

    assert len(handler.get_battles()) == 1
    assert battle.opponent == "npc"
    assert battle.outcome == OutputBattle.DRAW
    assert before <= battle.timestamp <= after


def test_get_last_battle(handler):
    assert handler.get_last_battle() is None

    handler.record_battle("npc", OutputBattle.WON)
    b2 = handler.record_battle("npc", OutputBattle.LOST)

    assert handler.get_last_battle() == b2


def test_has_fought_and_outcome_invalid(handler):
    handler.record_battle("npc", OutputBattle.WON)
    assert not handler.has_fought_and_outcome("invalid_outcome", "npc")


def test_encode_decode_battle(handler):
    handler.record_battle("npc", OutputBattle.WON)
    encoded = handler.encode_battle()

    new_handler = BattlesHandler("player")
    new_handler.decode_battle(NPCState(battles=encoded))

    assert len(new_handler.get_battles()) == 1
    assert new_handler.get_battles()[0].outcome == OutputBattle.WON


def test_decode_battle_with_legacy_placeholder():
    legacy_data = NPCState(
        battles=[
            {
                "fighter": "player",
                "opponent": "player",
                "outcome": OutputBattle.DRAW,
                "timestamp": time.time(),
                "instance_id": "1234567890abcdef1234567890abcdef",
            }
        ]
    )

    handler = BattlesHandler("hero")
    handler.decode_battle(legacy_data)

    battle = handler.get_battles()[0]
    assert battle.fighter == "hero"
    assert battle.opponent == "hero"


def test_decode_battle_empty(handler):
    handler.decode_battle(NPCState(battles=[]))
    assert handler.get_battles() == []


def test_record_battle_with_location_and_turns(handler):
    battle = handler.record_battle(
        "npc", OutputBattle.WON, location="forest", turns=3
    )
    assert battle.location == "forest"
    assert battle.turns == 3


def test_get_battles_by_location(handler):
    handler.record_battle("npc1", OutputBattle.WON, location="cave")
    handler.record_battle("npc2", OutputBattle.LOST, location="cave")
    handler.record_battle("npc3", OutputBattle.DRAW, location="forest")

    grouped = handler.get_battles_by_location()

    assert len(grouped["cave"]) == 2
    assert len(grouped["forest"]) == 1
    assert grouped["forest"][0].opponent == "npc3"


def test_default_location_and_turns(handler):
    battle = handler.record_battle("npc", OutputBattle.DRAW)
    assert battle.location == ""
    assert battle.turns == 1


def test_battle_outcome_summary_with_turns(handler):
    handler.record_battle("npc1", OutputBattle.WON, turns=2)
    handler.record_battle("npc2", OutputBattle.LOST, turns=4)

    summary = handler.get_battle_outcome_summary()

    assert summary["total"] == 2
    assert summary["won"] == 1
    assert summary["lost"] == 1
    assert summary["draw"] == 0
    assert summary["average_turns"] == 3
