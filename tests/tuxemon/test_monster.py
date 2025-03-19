# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon import prepare
from tuxemon.db import (
    AttributesModel,
    Modifier,
    ShapeModel,
    TechniqueModel,
    db,
)
from tuxemon.monster import Monster
from tuxemon.prepare import MAX_LEVEL
from tuxemon.taste import Taste
from tuxemon.technique.technique import Technique
from tuxemon.time_handler import today_ordinal


class MonsterTestBase(unittest.TestCase):
    pass


class SetLevel(MonsterTestBase):
    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"
        self.mon.set_level(2)

    def test_set_level(self):
        self.mon.set_level(5)
        self.assertEqual(self.mon.level, 5)

    def test_set_level_clamps_max(self):
        self.mon.set_level(10000)
        self.assertEqual(self.mon.level, MAX_LEVEL)

    def test_set_level_clamps_to_1(self):
        self.mon.set_level(-100)
        self.assertEqual(self.mon.level, 1)


class SetCapture(MonsterTestBase):
    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"
        self.mon.set_capture(today_ordinal())

    def test_set_capture_zero(self):
        self.mon.set_capture(0)
        self.assertEqual(self.mon.capture, today_ordinal())

    def test_set_capture_amount(self):
        self.mon.set_capture(5)
        self.assertEqual(self.mon.capture, 5)


class SetStats(MonsterTestBase):
    _shape_attr = AttributesModel(
        armour=7, dodge=5, hp=6, melee=6, ranged=6, speed=6
    )
    _shape = ShapeModel(slug="dragon", attributes=_shape_attr)

    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"
        self.mon.level = 5
        self.value = self.mon.level + prepare.COEFF_STATS
        self._shape_model = {"dragon": self._shape}
        db.database["shape"] = self._shape_model

        self.peppy = MagicMock(spec=Taste)
        self.peppy.slug = "peppy"
        self.peppy.taste_type = "warm"
        self.modifier1 = MagicMock(spec=Modifier)
        self.modifier1.attribute = "stat"
        self.modifier1.values = ["speed"]
        self.modifier1.multiplier = 1.1
        self.peppy.modifiers = [self.modifier1]

        self.mild = MagicMock(spec=Taste)
        self.mild.slug = "mild"
        self.mild.taste_type = "warm"
        self.modifier2 = MagicMock(spec=Modifier)
        self.modifier2.attribute = "stat"
        self.modifier2.values = ["speed"]
        self.modifier2.multiplier = 0.9
        self.mild.modifiers = [self.modifier2]

        self.flakey = MagicMock(spec=Taste)
        self.flakey.slug = "flakey"
        self.flakey.taste_type = "warm"
        self.modifier3 = MagicMock(spec=Modifier)
        self.modifier3.attribute = "stat"
        self.modifier3.values = ["ranged"]
        self.modifier3.multiplier = 0.9
        self.flakey.modifiers = [self.modifier3]

        self.refined = MagicMock(spec=Taste)
        self.refined.slug = "refined"
        self.refined.taste_type = "warm"
        self.modifier4 = MagicMock(spec=Modifier)
        self.modifier4.attribute = "stat"
        self.modifier4.values = ["dodge"]
        self.modifier4.multiplier = 1.1
        self.refined.modifiers = [self.modifier4]

        Taste._tastes = {}
        Taste._tastes["peppy"] = self.peppy
        Taste._tastes["mild"] = self.mild
        Taste._tastes["flakey"] = self.flakey
        Taste._tastes["refined"] = self.refined

    def tearDown(self):
        Taste.clear_cache()

    def test_set_stats_basic(self):
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value)
        self.assertEqual(self.mon.speed, self.value)
        self.assertEqual(self.mon.hp, self.value)

    def test_set_stats_shape(self):
        self.mon.shape = "dragon"
        self.mon.set_stats()
        _shape = self._shape.attributes
        self.assertEqual(self.mon.armour, _shape.armour * self.value)
        self.assertEqual(self.mon.dodge, _shape.dodge * self.value)
        self.assertEqual(self.mon.melee, _shape.melee * self.value)
        self.assertEqual(self.mon.ranged, _shape.ranged * self.value)
        self.assertEqual(self.mon.speed, _shape.speed * self.value)
        self.assertEqual(self.mon.hp, _shape.hp * self.value)

    def test_set_stats_taste_warm(self):
        self.mon.taste_warm = self.peppy.slug
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value)
        self.assertEqual(self.mon.speed, int(self.value * 1.1))  # Apply bonus
        self.assertEqual(self.mon.hp, self.value)

    def test_set_stats_taste_cold(self):
        self.mon.taste_cold = self.mild.slug
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value)
        self.assertEqual(self.mon.speed, int(self.value * 0.9))  # Apply malus
        self.assertEqual(self.mon.hp, self.value)

    def test_set_stats_tastes(self):
        self.mon.taste_cold = self.flakey.slug
        self.mon.taste_warm = self.refined.slug
        self.mon.set_stats()

        expected_dodge = int(self.value * 1.1)  # 10% bonus from refined
        expected_ranged = int(self.value * 0.9)  # 10% malus from flakey

        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, expected_dodge)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, expected_ranged)
        self.assertEqual(self.mon.speed, self.value)
        self.assertEqual(self.mon.hp, self.value)


class SetCharHeight(MonsterTestBase):
    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"

    def test_set_char_height(self):
        value = 10.0
        self.mon.set_char_height(value)
        lower, upper = prepare.HEIGHT_RANGE
        self.assertGreaterEqual(self.mon.height, lower * value)
        self.assertLessEqual(self.mon.height, upper * value)


class SetCharWeight(MonsterTestBase):
    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"

    def test_set_char_weight(self):
        value = 10.0
        self.mon.set_char_weight(value)
        lower, upper = prepare.WEIGHT_RANGE
        self.assertGreaterEqual(self.mon.weight, lower * value)
        self.assertLessEqual(self.mon.weight, upper * value)


class Learn(MonsterTestBase):
    _tech = TechniqueModel(
        tech_id=69,
        accuracy=0.85,
        flip_axes="",
        potency=0.0,
        power=1.5,
        range="melee",
        recharge=1,
        sfx="sfx_blaster",
        slug="ram",
        sort="damage",
        target={
            "enemy_monster": False,
            "enemy_team": False,
            "enemy_trainer": False,
            "own_monster": False,
            "own_team": False,
            "own_trainer": False,
        },
        types=[],
        category="simple",
        tags=["animal"],
        use_tech="combat_used_x",
        effects=[],
        modifiers=[],
    )

    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"
        self.mon.moves = []
        self._tech_model = {"ram": self._tech}
        db.database["technique"] = self._tech_model

    def test_learn(self):
        tech = Technique()
        tech.load("ram")
        self.mon.learn(tech)
        self.assertEqual(len(self.mon.moves), 1)
        move = self.mon.moves[0]
        self.assertEqual(move.slug, "ram")
        self.assertEqual(move.tech_id, 69)
        self.assertEqual(move.accuracy, 0.85)
        self.assertEqual(move.power, 1.5)
        self.assertEqual(move.potency, 0.0)
