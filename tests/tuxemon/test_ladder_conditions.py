# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

from tuxemon.event.conditions.monster_level import MonsterLevelCondition
from tuxemon.event.conditions.party_species import PartySpeciesCondition


def _make_monster(slug: str, level: int, instance_hex: str) -> MagicMock:
    monster = MagicMock()
    monster.slug = slug
    monster.level = level
    monster.instance_id.hex = instance_hex
    return monster


class TestPartySpeciesCondition:
    def test_two_distinct_species_greater_or_equal_2_true(self):
        monsters = [
            _make_monster("slime", 5, "aa"),
            _make_monster("slime", 6, "bb"),
            _make_monster("boar", 7, "cc"),
        ]
        session = MagicMock()
        session.player.monsters = monsters

        cond = PartySpeciesCondition(operator="greater_or_equal", count=2)
        assert cond.test(session) is True

    def test_two_distinct_species_greater_or_equal_3_false(self):
        monsters = [
            _make_monster("slime", 5, "aa"),
            _make_monster("slime", 6, "bb"),
            _make_monster("boar", 7, "cc"),
        ]
        session = MagicMock()
        session.player.monsters = monsters

        cond = PartySpeciesCondition(operator="greater_or_equal", count=3)
        assert cond.test(session) is False

    def test_two_distinct_species_equals_2_true(self):
        monsters = [
            _make_monster("slime", 5, "aa"),
            _make_monster("slime", 6, "bb"),
            _make_monster("boar", 7, "cc"),
        ]
        session = MagicMock()
        session.player.monsters = monsters

        cond = PartySpeciesCondition(operator="equals", count=2)
        assert cond.test(session) is True

    def test_empty_team_equals_0_true(self):
        session = MagicMock()
        session.player.monsters = []

        cond = PartySpeciesCondition(operator="equals", count=0)
        assert cond.test(session) is True


class TestMonsterLevelCondition:
    def test_stored_monster_level_10_greater_or_equal_10_true(self):
        target = _make_monster("slime", 10, "deadbeef")
        other = _make_monster("boar", 15, "cafebabe")
        session = MagicMock()
        session.player.monsters = [other, target]
        session.player.game_variables = MagicMock(
            get=lambda k, d=None: {"target_id": "deadbeef"}.get(k, d)
        )

        cond = MonsterLevelCondition(
            variable="target_id", operator="greater_or_equal", level=10
        )
        assert cond.test(session) is True

    def test_stored_monster_level_10_greater_than_10_false(self):
        target = _make_monster("slime", 10, "deadbeef")
        other = _make_monster("boar", 15, "cafebabe")
        session = MagicMock()
        session.player.monsters = [other, target]
        session.player.game_variables = MagicMock(
            get=lambda k, d=None: {"target_id": "deadbeef"}.get(k, d)
        )

        cond = MonsterLevelCondition(
            variable="target_id", operator="greater_than", level=10
        )
        assert cond.test(session) is False

    def test_stored_id_not_in_team_false(self):
        other = _make_monster("boar", 15, "cafebabe")
        session = MagicMock()
        session.player.monsters = [other]
        session.player.game_variables = MagicMock(
            get=lambda k, d=None: {"target_id": "deadbeef"}.get(k, d)
        )

        cond = MonsterLevelCondition(
            variable="target_id", operator="greater_or_equal", level=1
        )
        assert cond.test(session) is False

    def test_variable_not_set_false(self):
        target = _make_monster("slime", 10, "deadbeef")
        session = MagicMock()
        session.player.monsters = [target]
        session.player.game_variables = MagicMock(
            get=lambda k, d=None: {}.get(k, d)
        )

        cond = MonsterLevelCondition(
            variable="target_id", operator="greater_or_equal", level=5
        )
        assert cond.test(session) is False

    def test_same_slug_only_matching_hex_counts(self):
        other_same_slug = _make_monster("slime", 20, "aaaa")
        stored = _make_monster("slime", 5, "deadbeef")
        session = MagicMock()
        session.player.monsters = [other_same_slug, stored]
        session.player.game_variables = MagicMock(
            get=lambda k, d=None: {"target_id": "deadbeef"}.get(k, d)
        )

        cond = MonsterLevelCondition(
            variable="target_id", operator="greater_or_equal", level=10
        )
        assert cond.test(session) is False
