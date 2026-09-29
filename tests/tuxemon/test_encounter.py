# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random

import pytest

from tuxemon.db import EncounterType
from tuxemon.encounter import Encounter, EncounterResult, HordeEncounterResult


class DummyNPC:
    def __init__(self, avg_level=5, variables=None):
        self.party = type("Party", (), {"level_average": avg_level})
        self.game_variables = variables or {}


class DummyEncounterData:
    """Minimal stub for EncounterData that avoids DB lookups."""

    def __init__(self, slug="test-zone"):
        self.slug = slug
        self.encounter_type = EncounterType.SINGLE
        self.encounters = []
        self.horde = None
        self.scaling_zone = False
        self.override_level_range = None
        self.scale_offset_range = None
        self.scale_multiplier = 1.0

    def get_encounters(self):
        return self.encounters


class DummyEncounterItem:
    def __init__(
        self,
        monster="agnite",
        rate=100,
        level_range=(1, 5),
        held_items=None,
        scaling_enabled=False,
    ):
        self.monster = monster
        self.encounter_rate = rate
        self.level_range = level_range
        self.level_offset_range = None
        self.level_offset = 0
        self.held_items = held_items or []
        self.scaling_enabled = scaling_enabled
        self.min_player_level = None
        self.max_player_level = None
        self.variables = []
        self.override_level_range = None
        self.scaling_offset_range = None


class DummyHeldItem:
    def __init__(self, slug="potion", prob=100):
        self.item_slug = slug
        self.probability = prob


@pytest.mark.parametrize(
    "roll_value, expected",
    [
        pytest.param(0, True, id="low_roll_succeeds"),
        pytest.param(200, False, id="high_roll_fails"),
    ],
)
def test_probability_gate(monkeypatch, roll_value, expected):
    zone = DummyEncounterData()
    zone.encounters = [
        DummyEncounterItem(monster="agnite", rate=100, level_range=(1, 5))
    ]
    enc = Encounter(zone)

    monkeypatch.setattr(random, "uniform", lambda a, b: roll_value)
    monkeypatch.setattr(random, "choices", lambda seq, weights, k: [seq[0]])

    npc = DummyNPC()
    result = enc.get_single_encounter(npc, total_prob=100)
    assert (result is not None) == expected


def test_weighted_monster_selection(monkeypatch):
    zone = DummyEncounterData()
    agnite = DummyEncounterItem(monster="agnite", rate=10, level_range=(1, 5))
    pairagrin = DummyEncounterItem(
        monster="pairagrin", rate=90, level_range=(1, 5)
    )
    zone.encounters = [agnite, pairagrin]
    enc = Encounter(zone)

    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    monkeypatch.setattr(
        random,
        "choices",
        lambda seq, weights, k: [seq[weights.index(max(weights))]],
    )

    npc = DummyNPC()
    result = enc.get_single_encounter(npc, total_prob=100)
    assert result.monster.monster == "pairagrin"


def test_level_scaling(monkeypatch):
    zone = DummyEncounterData()
    zone.scaling_zone = True
    item = DummyEncounterItem(
        monster="rockitten",
        rate=100,
        level_range=(1, 10),
        scaling_enabled=True,
    )
    zone.encounters = [item]
    enc = Encounter(zone)

    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    monkeypatch.setattr(random, "choices", lambda seq, weights, k: [seq[0]])
    monkeypatch.setattr(random, "randint", lambda a, b: a)

    npc = DummyNPC(avg_level=10)
    result = enc.get_single_encounter(npc, total_prob=100)
    assert isinstance(result, EncounterResult)
    assert result.monster.monster == "rockitten"
    assert result.level >= 1


def test_held_item_selection(monkeypatch):
    zone = DummyEncounterData()
    item = DummyEncounterItem(
        monster="rat",
        rate=100,
        level_range=(1, 5),
        held_items=[DummyHeldItem("potion", 100)],
    )
    zone.encounters = [item]
    enc = Encounter(zone)

    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    monkeypatch.setattr(random, "choices", lambda seq, weights, k: [seq[0]])

    npc = DummyNPC()
    result = enc.get_single_encounter(npc, total_prob=100)
    assert isinstance(result, EncounterResult)
    assert result.held_item == "potion"


def test_horde_encounter(monkeypatch):
    zone = DummyEncounterData()
    zone.encounter_type = EncounterType.HORDE
    zone.horde = type(
        "HordeModel",
        (),
        {
            "monsters": [
                DummyEncounterItem(
                    monster="rockitten", rate=100, level_range=(1, 5)
                ),
                DummyEncounterItem(
                    monster="pairagrin", rate=100, level_range=(1, 5)
                ),
            ],
            "horde_level_range": None,
            "horde_exp_mod": None,
        },
    )()
    enc = Encounter(zone)

    monkeypatch.setattr(random, "uniform", lambda a, b: 0)
    monkeypatch.setattr(random, "randint", lambda a, b: a)

    npc = DummyNPC(avg_level=5)
    result = enc.get_horde_encounter(npc, total_prob=100)
    assert isinstance(result, HordeEncounterResult)
    assert len(result.monsters) == 2
    assert {r.monster.monster for r in result.monsters} == {
        "rockitten",
        "pairagrin",
    }
    assert result.horde_exp_mod is None
