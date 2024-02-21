# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon import formula, prepare
from tuxemon.db import (
    MonsterShape,
    ShapeModel,
    TasteCold,
    TasteWarm,
    TechniqueModel,
    db,
)
from tuxemon.monster import Monster
from tuxemon.prepare import MAX_LEVEL
from tuxemon.technique.technique import Technique


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
        self.mon.set_capture(formula.today_ordinal())

    def test_set_capture_zero(self):
        self.mon.set_capture(0)
        self.assertEqual(self.mon.capture, formula.today_ordinal())

    def test_set_capture_amount(self):
        self.mon.set_capture(5)
        self.assertEqual(self.mon.capture, 5)


class SetStats(MonsterTestBase):
    _shape = ShapeModel(
        slug="dragon", armour=7, dodge=5, hp=6, melee=6, ranged=6, speed=6
    )

    def setUp(self):
        self.mon = Monster()
        self.mon.name = "agnite"
        self.mon.level = 5
        self.value = self.mon.level + prepare.COEFF_STATS
        self.malus = int(self.value * prepare.TASTE_RANGE[0])
        self.bonus = int(self.value * prepare.TASTE_RANGE[1])
        self._shape_model = {"dragon": self._shape}
        db.database["shape"] = self._shape_model

    def test_set_stats_basic(self):
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value)
        self.assertEqual(self.mon.speed, self.value)
        self.assertEqual(self.mon.hp, self.value)

    def test_set_stats_shape(self):
        self.mon.shape = MonsterShape.dragon
        self.mon.set_stats()
        _shape = self._shape
        self.assertEqual(self.mon.armour, _shape.armour * self.value)
        self.assertEqual(self.mon.dodge, _shape.dodge * self.value)
        self.assertEqual(self.mon.melee, _shape.melee * self.value)
        self.assertEqual(self.mon.ranged, _shape.ranged * self.value)
        self.assertEqual(self.mon.speed, _shape.speed * self.value)
        self.assertEqual(self.mon.hp, _shape.hp * self.value)

    def test_set_stats_taste_warm(self):
        self.mon.taste_warm = TasteWarm.peppy
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value)
        self.assertEqual(self.mon.speed, self.value + self.bonus)
        self.assertEqual(self.mon.hp, self.value)

    def test_set_stats_taste_cold(self):
        self.mon.taste_cold = TasteCold.mild
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value)
        self.assertEqual(self.mon.speed, self.value + self.malus)
        self.assertEqual(self.mon.hp, self.value)

    def test_set_stats_tastes(self):
        self.mon.taste_cold = TasteCold.flakey
        self.mon.taste_warm = TasteWarm.refined
        self.mon.set_stats()
        self.assertEqual(self.mon.armour, self.value)
        self.assertEqual(self.mon.dodge, self.value + self.bonus)
        self.assertEqual(self.mon.melee, self.value)
        self.assertEqual(self.mon.ranged, self.value + self.malus)
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
        target={},
        types=[],
        use_tech="combat_used_x",
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
