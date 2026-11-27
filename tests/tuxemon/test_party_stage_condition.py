# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

from tuxemon.db import EvolutionStage
from tuxemon.event.conditions.party_stage import PartyStageCondition


def _session(*stages):
    session = MagicMock()
    monsters = []
    for stage in stages:
        monster = MagicMock()
        monster.stage = stage
        monsters.append(monster)
    session.player.monsters = monsters
    return session


class TestPartyStageCondition:
    def test_one_evolved_among_basics_true(self):
        session = _session(
            EvolutionStage.BASIC, EvolutionStage.STAGE1, EvolutionStage.BASIC
        )
        cond = PartyStageCondition(
            stages="stage1:stage2", operator="greater_or_equal", count=1
        )
        assert cond.test(session) is True

    def test_only_basic_and_standalone_false(self):
        session = _session(EvolutionStage.BASIC, EvolutionStage.STANDALONE)
        cond = PartyStageCondition(
            stages="stage1:stage2", operator="greater_or_equal", count=1
        )
        assert cond.test(session) is False

    def test_six_stage2_true(self):
        session = _session(*[EvolutionStage.STAGE2] * 6)
        cond = PartyStageCondition(
            stages="stage2", operator="greater_or_equal", count=6
        )
        assert cond.test(session) is True

    def test_five_stage2_and_a_stage1_false(self):
        session = _session(*[EvolutionStage.STAGE2] * 5, EvolutionStage.STAGE1)
        cond = PartyStageCondition(
            stages="stage2", operator="greater_or_equal", count=6
        )
        assert cond.test(session) is False

    def test_plain_string_stages_count(self):
        session = _session("stage1", "basic")
        cond = PartyStageCondition(stages="stage1", operator="equals", count=1)
        assert cond.test(session) is True

    def test_empty_team_equals_0_true(self):
        session = _session()
        cond = PartyStageCondition(stages="stage2", operator="equals", count=0)
        assert cond.test(session) is True
