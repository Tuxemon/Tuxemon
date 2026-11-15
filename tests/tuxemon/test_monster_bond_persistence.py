# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tuxemon.db import GenderType, MonsterModel
from tuxemon.monster.monster import Monster
from tuxemon.taste import Taste
from tuxemon.technique.technique import Technique


@pytest.fixture
def monster_factory(monkeypatch):
    original_init = Monster.__init__

    monkeypatch.setattr(
        Taste, "generate", classmethod(lambda cls, *args: ("sweet", "salty"))
    )

    def fake_monster_init(
        self, slug="testmon", db_data=None, instance_id=None
    ):
        if db_data is None:
            db_data = MonsterModel.lookup(slug, None)
        original_init(self, slug, db_data, instance_id)

    monkeypatch.setattr(Monster, "__init__", fake_monster_init)

    def fake_init_assets(self, db_data):
        self.flair_slugs = set()
        self.flairs = {}

    monkeypatch.setattr(Monster, "_init_assets", fake_init_assets)

    fake_species_data = MagicMock()
    fake_species_data.species = "test"
    fake_species_data.stage = "basic"
    fake_species_data.tags = []
    fake_species_data.terrains = []
    fake_species_data.max_moves = 4
    fake_species_data.txmn_id = 0
    fake_species_data.catch_rate = 100
    fake_species_data.upper_catch_resistance = 1.0
    fake_species_data.lower_catch_resistance = 1.0
    fake_species_data.gender_weights = {GenderType.NEUTER: 1.0}
    fake_species_data.types = []
    fake_species_data.shape = "blob"
    fake_species_data.randomly = False
    fake_species_data.evolutions = []
    fake_species_data.history = []
    tech = MagicMock(spec=Technique, slug="ram")
    fake_species_data.moves = MagicMock()
    fake_species_data.moves.moves = [tech]
    fake_species_data.flairs = set()
    fake_species_data.sprites = MagicMock()
    fake_species_data.sounds = None
    fake_species_data.height = 1.0
    fake_species_data.weight = 1.0

    monkeypatch.setattr(
        MonsterModel, "lookup", lambda slug, db: fake_species_data
    )

    return Monster


def test_bond_survives_a_save_round_trip(monster_factory):
    monster = monster_factory()
    monster.bond_handler.bond = 77

    restored = monster_factory.from_save(monster.get_state())

    assert restored.bond_handler.bond == 77


def test_saved_bond_uses_the_format_the_handler_reads(monster_factory):
    monster = monster_factory()
    monster.bond_handler.bond = 42

    assert monster.get_state()["bond_dict"] == {"bond": 42}
