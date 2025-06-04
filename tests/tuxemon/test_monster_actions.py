# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.db import (
    AttributesModel,
    ElementModel,
    EvolutionStage,
    MonsterModel,
    ShapeModel,
    StatusModel,
    TechniqueModel,
    db,
)
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.surfanim import FlipAxes
from tuxemon.tuxepedia import Tuxepedia


def mockPlayer(self) -> None:
    self.name = "Jeff"
    self.game_variables = {}
    self.tuxepedia = Tuxepedia()


class TestMonsterActions(unittest.TestCase):
    _dragon_attr = AttributesModel(
        armour=7, dodge=5, hp=6, melee=6, ranged=6, speed=6
    )
    _dragon = ShapeModel(slug="dragon", attributes=_dragon_attr)
    _blob_attr = AttributesModel(
        armour=8, dodge=4, hp=8, melee=4, ranged=8, speed=4
    )
    _blob = ShapeModel(slug="blob", attributes=_blob_attr)
    _fire = ElementModel(
        slug="fire", icon="gfx/ui/icons/element/fire_type.png", types=[]
    )
    _metal = ElementModel(
        slug="metal", icon="gfx/ui/icons/element/metal_type.png", types=[]
    )
    _agnite = MonsterModel(
        slug="agnite",
        category="false_dragon",
        moveset=[{"level_learned": 1, "technique": "ram"}],
        evolutions=[],
        history=[],
        tags=[],
        terrains=["coastal", "desert", "mountains"],
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
        moveset=[{"level_learned": 1, "technique": "ram"}],
        evolutions=[],
        history=[],
        tags=[],
        terrains=[],
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
    _faint = StatusModel(
        effects=[],
        modifiers=[],
        flip_axes=FlipAxes.NONE,
        icon="gfx/ui/icons/status/icon_faint.png",
        sfx="sfx_faint",
        slug="faint",
        range="special",
        sort="meta",
        cond_id=0,
    )

    _ram = TechniqueModel(
        tech_id=69,
        accuracy=0.85,
        flip_axes=FlipAxes.NONE,
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
        use_tech="combat_used_x",
        tags=["animal"],
        category="simple",
        effects=[],
        modifiers=[],
    )

    def setUp(self):
        action = ActionManager()
        condition = ConditionManager()
        self.mock_screen = MagicMock()
        local_session.set_client(MagicMock())
        local_session.client.event_engine = EventEngine(
            local_session, action, condition
        )
        with patch.object(Player, "__init__", mockPlayer):
            self.action = local_session.client.event_engine
            local_session.set_player(Player())
            self.player = local_session.player
            self.player.monsters = []
            self._monster_model = {"agnite": self._agnite}
            self._monster_model["nut"] = self._nut
            self._shape_model = {"dragon": self._dragon}
            self._shape_model["blob"] = self._blob
            self._element_model = {"fire": self._fire}
            self._element_model["metal"] = self._metal
            self._condition_model = {"faint": self._faint}
            self._technique_model = {"ram": self._ram}
            db.database["monster"] = self._monster_model
            db.database["shape"] = self._shape_model
            db.database["element"] = self._element_model
            db.database["status"] = self._condition_model
            db.database["technique"] = self._technique_model

    def test_add_monster(self):
        _params = ["agnite", 5]
        self.action.execute_action("add_monster", _params)
        self.assertEqual(len(self.player.monsters), 1)
        self.assertEqual(self.player.monsters[0].slug, "agnite")

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

    def test_give_experience(self):
        _params = [5]
        self.action.execute_action("random_monster", _params)
        before = self.player.monsters[0].total_experience
        _params = [None, None]
        self.action.execute_action("give_experience", _params)
        after = self.player.monsters[0].total_experience
        self.assertEqual(after, before)

    def test_give_experience_number_negative(self):
        _params = [5]
        self.action.execute_action("random_monster", _params)
        before = self.player.monsters[0].total_experience
        _params = [None, -50]
        self.action.execute_action("give_experience", _params)
        after = self.player.monsters[0].total_experience
        self.assertEqual(after, before)

    def test_give_experience_number_positive(self):
        _params = [5]
        self.action.execute_action("random_monster", _params)
        before = self.player.monsters[0].total_experience
        _params = [None, 50]
        self.action.execute_action("give_experience", _params)
        after = self.player.monsters[0].total_experience
        self.assertEqual(after, before + 50)

    def test_give_experience_number_variable(self):
        _params = [5]
        self.action.execute_action("random_monster", _params)
        self.action.execute_action("set_variable", ["exp:50"])
        before = self.player.monsters[0].total_experience
        _params = [None, "exp"]
        self.action.execute_action("give_experience", _params)
        after = self.player.monsters[0].total_experience
        self.assertEqual(after, before + 50)
