# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.database.rules import config_monster
from tuxemon.database.runtime import db
from tuxemon.db import GenderType
from tuxemon.monster.monster import Monster
from tuxemon.monster.stats import IndividualValues
from tuxemon.shape import ShapeHandler
from tuxemon.taste import Taste


@pytest.fixture
def monster(monkeypatch):
    original_init = Monster.__init__

    Taste._tastes = {}

    class FakeDB:
        species = "testspecies"
        stage = None
        tags = []
        terrains = []
        max_moves = 4
        txmn_id = 0
        catch_rate = 100
        upper_catch_resistance = 1.0
        lower_catch_resistance = 1.0
        gender_weights = {GenderType.NEUTER: 1.0}
        types = []
        shape = None
        randomly = False
        evolutions = []
        history = []
        moveset = []
        flairs = []
        sprites = None
        sounds = None
        height = 1.0
        weight = 1.0

    def fake_init(self, slug="testmon", db_data=None, instance_id=None):
        original_init(self, slug, db_data or FakeDB(), instance_id)

    monkeypatch.setattr(Monster, "__init__", fake_init)
    monkeypatch.setattr(Monster, "_init_assets", lambda self, db_data: None)

    m = Monster()
    m.name = "agnite"
    m.individual_values = IndividualValues()
    return m


@pytest.mark.parametrize(
    "input_level,expected",
    [
        pytest.param(5, 5, id="normal"),
        pytest.param(10000, config_monster.level_range[1], id="high"),
        pytest.param(-100, 1, id="low"),
    ],
)
def test_set_level(monster, input_level, expected):
    monster.set_level(input_level, input_level)
    assert monster.level == expected


@pytest.fixture
def shape_model(monkeypatch):
    """Inject a fake shape model into the DB."""
    attr = MagicMock(armour=7, dodge=5, hp=6, melee=6, ranged=6, speed=6)
    shape = MagicMock(slug="dragon", attributes=attr)
    monkeypatch.setitem(db.database, "shape", {"dragon": shape})
    return shape


@pytest.fixture
def tastes(monkeypatch):
    """Inject fake tastes with modifiers."""
    Taste._tastes = {}

    def make_taste(slug, values, mult):
        t = MagicMock(spec=Taste)
        t.slug = slug
        t.taste_type = "warm"

        mod = MagicMock()
        mod.values = values
        mod.multiplier = mult
        t.modifiers = [mod]

        def get_multiplier(stat_name):
            m = 1.0
            for mod in t.modifiers:
                if stat_name in mod.values:
                    m *= mod.multiplier
            return m

        def apply_to_stat(stat_name, value):
            return round(value * get_multiplier(stat_name))

        t.get_multiplier.side_effect = get_multiplier
        t.apply_to_stat.side_effect = apply_to_stat

        Taste._tastes[slug] = t
        return t

    return {
        "peppy": make_taste("peppy", ["speed"], 1.1),
        "mild": make_taste("mild", ["speed"], 0.9),
        "flakey": make_taste("flakey", ["ranged"], 0.9),
        "refined": make_taste("refined", ["dodge"], 1.1),
    }


def test_set_stats_basic(monster):
    monster.set_level(5, 5)
    value = monster.level + config_monster.coeff_stats
    monster.set_stats()

    assert monster.armour == value
    assert monster.dodge == value
    assert monster.melee == value
    assert monster.ranged == value
    assert monster.speed == value
    assert monster.hp == value


def test_set_stats_shape(monster, shape_model):
    monster.set_level(5, 5)
    value = monster.level + config_monster.coeff_stats

    monster.shape = ShapeHandler("dragon")
    monster.set_stats()

    attr = shape_model.attributes
    assert monster.armour == attr.armour * value
    assert monster.dodge == attr.dodge * value
    assert monster.melee == attr.melee * value
    assert monster.ranged == attr.ranged * value
    assert monster.speed == attr.speed * value
    assert monster.hp == attr.hp * value


def test_set_stats_taste_warm(monster, tastes):
    monster.set_level(5, 5)
    value = monster.level + config_monster.coeff_stats

    monster.taste_warm = "peppy"
    monster.set_stats()

    assert monster.speed == round(value * 1.1)


def test_set_stats_taste_cold(monster, tastes):
    monster.set_level(5, 5)
    value = monster.level + config_monster.coeff_stats

    monster.taste_cold = "mild"
    monster.set_stats()

    assert monster.speed == round(value * 0.9)


def test_set_stats_tastes(monster, tastes):
    monster.set_level(5, 5)
    value = monster.level + config_monster.coeff_stats

    monster.taste_cold = "flakey"
    monster.taste_warm = "refined"
    monster.set_stats()

    assert monster.dodge == round(value * 1.1)
    assert monster.ranged == round(value * 0.9)
