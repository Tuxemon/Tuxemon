# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest import mock

from tuxemon import prepare
from tuxemon.client import LocalPygameClient
from tuxemon.db import (
    ConditionModel,
    ElementModel,
    EvolutionStage,
    MonsterModel,
    ShapeModel,
    db,
)
from tuxemon.player import Player
from tuxemon.session import local_session


def mockPlayer(self) -> None:
    self.name = "Jeff"
    self.money = {}
    self.game_variables = {}
    self.tuxepedia = {}


class TestMonsterActions(unittest.TestCase):
    _dragon = ShapeModel(
        slug="dragon", armour=7, dodge=5, hp=6, melee=6, ranged=6, speed=6
    )
    _blob = ShapeModel(
        slug="blob", armour=8, dodge=4, hp=8, melee=4, ranged=8, speed=4
    )
    _fire = ElementModel(
        slug="fire", icon="gfx/ui/icons/element/fire_type.png", types=[]
    )
    _metal = ElementModel(
        slug="metal", icon="gfx/ui/icons/element/metal_type.png", types=[]
    )
    _agnite = MonsterModel(
        slug="agnite",
        category="false_dragon",
        moveset=[],
        evolutions=[],
        history=[],
        shape="dragon",
        stage="basic",
        types=["fire"],
        possible_genders=["male", "female"],
        txmn_id=13,
        height=80,
        weight=24,
        catch_rate=100.0,
        lower_catch_resistance=0.95,
        upper_catch_resistance=1.25,
    )
    _nut = MonsterModel(
        slug="nut",
        category="hardware",
        moveset=[],
        evolutions=[],
        history=[],
        shape="blob",
        stage="basic",
        types=["metal"],
        possible_genders=["neuter"],
        txmn_id=4,
        height=45,
        weight=4,
        catch_rate=100.0,
        lower_catch_resistance=0.95,
        upper_catch_resistance=1.25,
    )
    _faint = ConditionModel(
        flip_axes="",
        sfx="sfx_faint",
        slug="faint",
        range="special",
        sort="meta",
        target={},
        cond_id=0,
    )

    def setUp(self):
        with mock.patch.object(Player, "__init__", mockPlayer):
            local_session.client = LocalPygameClient(prepare.CONFIG)
            self.action = local_session.client.event_engine
            local_session.player = Player()
            self.player = local_session.player
            self.player.monsters = []
            self.player.monster_boxes = {}
            self._monster_model = {"agnite": self._agnite}
            self._monster_model["nut"] = self._nut
            self._shape_model = {"dragon": self._dragon}
            self._shape_model["blob"] = self._blob
            self._element_model = {"fire": self._fire}
            self._element_model["metal"] = self._metal
            self._condition_model = {"faint": self._faint}
            db.database["monster"] = self._monster_model
            db.database["shape"] = self._shape_model
            db.database["element"] = self._element_model
            db.database["condition"] = self._condition_model

    def test_add_monster(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.assertEqual(len(self.player.monsters), 1)
        self.assertEqual(self.player.monsters[0].slug, "agnite")

    def test_set_monster_health(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.action.execute_action("set_monster_health", [])
        monster = self.player.monsters[0]
        self.assertEqual(monster.current_hp, monster.hp)

    def test_set_monster_health_positive_int(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.action.execute_action("set_monster_health", [None, 420])
        monster = self.player.monsters[0]
        self.assertEqual(monster.current_hp, monster.hp)

    def test_set_monster_health_negative_int(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.action.execute_action("set_monster_health", [None, -420])
        monster = self.player.monsters[0]
        self.assertEqual(monster.current_hp, 0)
        self.assertEqual(len(monster.status), 1)

    def test_set_monster_health_positive_float(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.action.execute_action("set_monster_health", [None, 0.5])
        monster = self.player.monsters[0]
        self.assertEqual(monster.current_hp, monster.hp)

    def test_set_monster_health_negative_float(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.action.execute_action("set_monster_health", [None, -0.5])
        monster = self.player.monsters[0]
        self.assertEqual(monster.current_hp, monster.hp / 2)

    def test_set_monster_status(self):
        self.player.steps = 0.0
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        self.action.execute_action("set_monster_health", [None, -420])
        self.assertEqual(len(monster.status), 1)
        self.action.execute_action("set_monster_status", [])
        self.assertEqual(len(monster.status), 0)

    def test_modify_monster_stats(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        _armour = monster.armour + 1
        _dodge = monster.dodge + 1
        _hp = monster.hp + 1
        _melee = monster.melee + 1
        _speed = monster.speed + 1
        _ranged = monster.ranged + 1
        self.action.execute_action("modify_monster_stats", [])
        self.assertEqual(monster.armour, _armour)
        self.assertEqual(monster.dodge, _dodge)
        self.assertEqual(monster.hp, _hp)
        self.assertEqual(monster.melee, _melee)
        self.assertEqual(monster.speed, _speed)
        self.assertEqual(monster.ranged, _ranged)

    def test_modify_monster_stats_int(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.armour
        before += monster.dodge
        before += monster.hp
        before += monster.melee
        before += monster.speed
        before += monster.ranged
        _params = [None, None, 10]
        self.action.execute_action("modify_monster_stats", _params)
        after = monster.armour
        after += monster.dodge
        after += monster.hp
        after += monster.melee
        after += monster.speed
        after += monster.ranged
        self.assertEqual(after, before + 60)

    def test_modify_monster_stats_float(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.armour
        before += monster.dodge
        before += monster.hp
        before += monster.melee
        before += monster.speed
        before += monster.ranged
        _params = [None, None, -0.25]
        self.action.execute_action("modify_monster_stats", _params)
        after = monster.armour
        after += monster.dodge
        after += monster.hp
        after += monster.melee
        after += monster.speed
        after += monster.ranged
        self.assertGreaterEqual(after, before * 0.75 - 1.25)
        self.assertLessEqual(after, before * 0.75 + 1.25)

    def test_modify_monster_stats_wrong_stat(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        _params = [None, "jimmy", -0.25]
        with self.assertRaises(ValueError):
            self.action.execute_action("modify_monster_stats", _params)

    def test_modify_monster_stats_right_stat(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.speed + 1
        self.action.execute_action("modify_monster_stats", [None, "speed"])
        self.assertEqual(monster.speed, before)

    def test_modify_monster_stats_random_positive(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.speed
        _params = [None, "speed", None, 1, 5]
        self.action.execute_action("modify_monster_stats", _params)
        self.assertGreaterEqual(monster.speed, before + 1)
        self.assertLessEqual(monster.speed, before + 5)

    def test_modify_monster_stats_random_negative(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.speed
        _params = [None, "speed", None, -5, -1]
        self.action.execute_action("modify_monster_stats", _params)
        self.assertGreaterEqual(monster.speed, before - 5)
        self.assertLessEqual(monster.speed, before - 1)

    def test_modify_monster_bond(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.bond + 1
        self.action.execute_action("modify_monster_bond", [])
        self.assertEqual(monster.bond, before)

    def test_modify_monster_bond_int(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.bond + 50
        self.action.execute_action("modify_monster_bond", [None, 50])
        self.assertEqual(monster.bond, before)
        self.action.execute_action("modify_monster_bond", [None, 50])
        self.assertEqual(monster.bond, prepare.BOND_RANGE[1])
        self.action.execute_action("modify_monster_bond", [None, -200])
        self.assertEqual(monster.bond, prepare.BOND_RANGE[0])

    def test_modify_monster_bond_float(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.bond + (monster.bond * 0.5)
        self.action.execute_action("modify_monster_bond", [None, 0.5])
        self.assertGreaterEqual(monster.bond, before - 0.5)
        self.assertLessEqual(monster.bond, before + 0.5)

    def test_modify_monster_bond_random_positive(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.bond
        _params = [None, None, 1, 5]
        self.action.execute_action("modify_monster_bond", _params)
        self.assertGreaterEqual(monster.bond, before + 1)
        self.assertLessEqual(monster.bond, before + 5)

    def test_modify_monster_bond_random_negative(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        monster = self.player.monsters[0]
        before = monster.bond
        _params = [None, None, -5, -1]
        self.action.execute_action("modify_monster_bond", _params)
        self.assertGreaterEqual(monster.bond, before - 5)
        self.assertLessEqual(monster.bond, before - 1)

    def test_random_monster(self):
        _params = [5]
        self.action.execute_action("random_monster", _params)
        self.assertEqual(len(self.player.monsters), 1)
        _container = ["nut", "agnite"]
        self.assertIn(self.player.monsters[0].slug, _container)

    def test_random_monster_experience(self):
        _params = [5, None, 69]
        self.action.execute_action("random_monster", _params)
        self.assertEqual(self.player.monsters[0].experience_modifier, 69)

    def test_random_monster_money(self):
        _params = [5, None, None, 69]
        self.action.execute_action("random_monster", _params)
        self.assertEqual(self.player.monsters[0].money_modifier, 69)

    def test_random_monster_shape(self):
        _params = [5, None, None, None, "blob"]
        self.action.execute_action("random_monster", _params)
        self.assertEqual(self.player.monsters[0].slug, "nut")

    def test_random_monster_shape_wrong(self):
        _params = [5, None, None, None, "chad"]
        with self.assertRaises(ValueError):
            self.action.execute_action("random_monster", _params)

    def test_random_monster_evolution(self):
        _params = [5, None, None, None, None, "basic"]
        _basic = EvolutionStage.basic
        self.action.execute_action("random_monster", _params)
        self.assertEqual(self.player.monsters[0].stage, _basic)

    def test_random_monster_evolution_wrong(self):
        _params = [5, None, None, None, None, "stage69"]
        with self.assertRaises(ValueError):
            self.action.execute_action("random_monster", _params)
