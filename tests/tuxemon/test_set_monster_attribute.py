# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.database.rules import config_monster
from tuxemon.db import Acquisition, GenderType, MonsterModel
from tuxemon.event.actions.set_monster_attribute import (
    SetMonsterAttributeAction,
)
from tuxemon.monster.monster import Monster
from tuxemon.taste import Taste
from tuxemon.technique.technique import Technique

BOND_ACQUISITION = {
    "unknown": 25,
    "captured": 25,
    "traded": 10,
    "bred": 40,
    "gifted": 30,
    "purchased": 20,
    "rescued": 35,
    "created": 25,
}


@pytest.fixture
def monster(monkeypatch):
    original_init = Monster.__init__

    def fake_monster_init(
        self, slug="testmon", db_data=None, instance_id=None
    ):
        if db_data is None:
            db_data = MonsterModel.lookup(slug, None)
        original_init(self, slug, db_data, instance_id)

    monkeypatch.setattr(Monster, "__init__", fake_monster_init)
    monkeypatch.setattr(Monster, "_init_assets", lambda self, db_data: None)
    # Pin the table: other tests mutate the shared config without restoring
    # it, and an empty table would make every acquisition yield the default.
    monkeypatch.setattr(config_monster, "bond_acquisition", BOND_ACQUISITION)
    monkeypatch.setattr(
        Taste, "generate", classmethod(lambda cls, *args: ("sweet", "salty"))
    )

    species = MagicMock()
    species.species = "test"
    species.stage = "basic"
    species.tags = []
    species.terrains = []
    species.max_moves = 4
    species.txmn_id = 0
    species.catch_rate = 100
    species.upper_catch_resistance = 1.0
    species.lower_catch_resistance = 1.0
    species.gender_weights = {GenderType.NEUTER: 1.0}
    species.types = []
    species.shape = "blob"
    species.randomly = False
    species.evolutions = []
    species.history = []
    species.moves = MagicMock()
    species.moves.moves = [MagicMock(spec=Technique, slug="ram")]
    species.flairs = set()
    species.sprites = MagicMock()
    species.sounds = None
    species.height = 1.0
    species.weight = 1.0
    monkeypatch.setattr(MonsterModel, "lookup", lambda slug, db: species)

    return Monster()


def _run(monster: Monster, attribute: str, value: str) -> None:
    session = MagicMock()
    session.player.game_variables = {"add_monster": str(monster.instance_id)}
    session.client.get_monster_by_iid.return_value = monster
    SetMonsterAttributeAction("add_monster", attribute, value).start(session)


@pytest.mark.parametrize(
    "value", [pytest.param(a.value, id=a.value) for a in Acquisition]
)
def test_acquisition_matches_python_api(monster, value):
    reference = Monster()
    reference.set_acquisition(Acquisition(value))

    _run(monster, "acquisition", value)

    assert monster.acquisition == Acquisition(value)
    assert monster.bond_handler.bond == reference.bond_handler.bond


def test_acquisition_reseeds_bond_from_config(monster):
    expected = config_monster.bond_acquisition["gifted"]
    assert monster.bond_handler.bond != expected

    _run(monster, "acquisition", "gifted")

    assert monster.acquisition == Acquisition.GIFTED
    assert monster.bond_handler.bond == expected


def test_invalid_acquisition_is_ignored(monster):
    bond = monster.bond_handler.bond

    _run(monster, "acquisition", "not_a_method")

    assert monster.acquisition == Acquisition.UNKNOWN
    assert monster.bond_handler.bond == bond


def test_other_attributes_still_use_plain_setattr(monster):
    bond = monster.bond_handler.bond

    _run(monster, "name", "Fluffy")

    assert monster.name == "Fluffy"
    assert monster.bond_handler.bond == bond
