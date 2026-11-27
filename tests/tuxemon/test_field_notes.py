# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import types

import pytest

from tuxemon.combat.field_notes import (
    KNOWN_MATCHUPS,
    KNOWN_RANGES,
    known_matchups,
    known_ranges,
    learn_from_hit,
    record_matchups,
    record_range,
)


class Vars(dict):
    def set(self, key, value):
        self[key] = value


@pytest.fixture
def character():
    return types.SimpleNamespace(game_variables=Vars())


class TestFreshCharacter:
    def test_known_matchups_empty(self, character):
        assert known_matchups(character) == set()

    def test_known_ranges_empty(self, character):
        assert known_ranges(character) == set()


class TestRecordMatchups:
    def test_single_pair(self, character):
        new = record_matchups(character, ["fire"], ["wood"])
        assert new == [("fire", "wood")]
        assert known_matchups(character) == {("fire", "wood")}
        assert character.game_variables[KNOWN_MATCHUPS] == "fire>wood"

    def test_duplicate_returns_empty(self, character):
        record_matchups(character, ["fire"], ["wood"])
        stored = character.game_variables[KNOWN_MATCHUPS]
        new = record_matchups(character, ["fire"], ["wood"])
        assert new == []
        assert character.game_variables[KNOWN_MATCHUPS] == stored

    def test_two_by_two(self, character):
        new = record_matchups(character, ["fire", "water"], ["wood", "metal"])
        assert new == [
            ("fire", "metal"),
            ("fire", "wood"),
            ("water", "metal"),
            ("water", "wood"),
        ]
        assert known_matchups(character) == {
            ("fire", "metal"),
            ("fire", "wood"),
            ("water", "metal"),
            ("water", "wood"),
        }

    def test_half_known_returns_only_new(self, character):
        record_matchups(character, ["fire"], ["wood"])
        new = record_matchups(character, ["fire"], ["wood", "metal"])
        assert new == [("fire", "metal")]
        assert known_matchups(character) == {
            ("fire", "wood"),
            ("fire", "metal"),
        }

    def test_stored_string_sorted(self, character):
        record_matchups(character, ["water"], ["fire"])
        record_matchups(character, ["fire"], ["wood"])
        assert (
            character.game_variables[KNOWN_MATCHUPS] == "fire>wood,water>fire"
        )

    def test_ignores_junk_entries(self, character):
        character.game_variables[KNOWN_MATCHUPS] = "fire>wood,,junk,>x,y>"
        assert known_matchups(character) == {("fire", "wood")}


class TestRecordRange:
    def test_new_then_existing(self, character):
        assert record_range(character, "melee") is True
        assert record_range(character, "melee") is False
        assert known_ranges(character) == {"melee"}

    def test_empty_range_rejected(self, character):
        assert record_range(character, "") is False

    def test_two_ranges_sorted(self, character):
        record_range(character, "ranged")
        record_range(character, "melee")
        assert character.game_variables[KNOWN_RANGES] == "melee,ranged"


class Bag:
    def __init__(self, slugs):
        self.slugs = set(slugs)

    def has_item(self, slug):
        return slug in self.slugs


def _with_bag(slugs):
    return types.SimpleNamespace(game_variables=Vars(), bag=Bag(slugs))


class TestAppGate:
    def test_with_app_records_and_reports(self):
        c = _with_bag(["app_field_notes"])
        assert learn_from_hit(c, ["fire"], ["wood"], "melee") is True
        assert known_matchups(c) == {("fire", "wood")}
        assert known_ranges(c) == {"melee"}
        assert learn_from_hit(c, ["fire"], ["wood"], "melee") is False

    def test_without_app_records_nothing(self):
        c = _with_bag(["potion"])
        assert learn_from_hit(c, ["fire"], ["wood"], "melee") is False
        assert KNOWN_MATCHUPS not in c.game_variables
        assert KNOWN_RANGES not in c.game_variables
