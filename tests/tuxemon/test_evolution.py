# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import patch

from tuxemon.db import (
    ElementModel,
    MonsterEvolutionItemModel,
    TechniqueModel,
    db,
)
from tuxemon.element import Element
from tuxemon.monster import Monster
from tuxemon.player import Player
from tuxemon.session import local_session
from tuxemon.surfanim import FlipAxes
from tuxemon.technique.technique import Technique

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

_strike = TechniqueModel(
    tech_id=69,
    accuracy=0.85,
    flip_axes=FlipAxes.NONE,
    potency=0.0,
    power=1.5,
    range="melee",
    recharge=1,
    sfx="sfx_blaster",
    slug="strike",
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

_metal = ElementModel(
    slug="metal", icon="gfx/ui/icons/element/metal_type.png", types=[]
)


def mockPlayer(self) -> None:
    _tech_model = {"ram": _ram, "strike": _strike}
    _element_model = {"metal": _metal}
    db.database["technique"] = _tech_model
    db.database["element"] = _element_model
    self.name = "Jeff"
    self.game_variables = {}
    member1 = Monster()
    member1.slug = "nut"
    member2 = Monster()
    member2.slug = "rockitten"
    tech = Technique.create("ram")
    member1.learn(tech)
    self.monsters = [member1, member2]


class TestCanEvolve(unittest.TestCase):
    def setUp(self):
        self.mon = Monster()
        with patch.object(Player, "__init__", mockPlayer):
            local_session.set_player(Player())
            self.player = local_session.player

    def test_no_owner(self):
        self.mon.owner = None
        evo = MonsterEvolutionItemModel(monster_slug="rockat")
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_level_too_low(self):
        self.mon.level = 10
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(monster_slug="rockat", at_level=20)
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_level_meets_requirement(self):
        self.mon.owner = self.player
        self.mon.level = 20
        evo = MonsterEvolutionItemModel(monster_slug="rockat", at_level=20)
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_gender_mismatch(self):
        self.mon.owner = self.player
        self.mon.gender = "male"
        evo = MonsterEvolutionItemModel(monster_slug="rockat", gender="female")
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_gender_match(self):
        self.mon.owner = self.player
        self.mon.gender = "male"
        evo = MonsterEvolutionItemModel(monster_slug="rockat", gender="male")
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_inside_mismatch(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(monster_slug="rockat", inside=True)
        context = {"map_inside": False}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_inside_match(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(monster_slug="rockat", inside=True)
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_all_conditions_met(self):
        self.mon.owner = self.player
        self.mon.level = 20
        self.mon.gender = "male"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", at_level=20, gender="male", inside=True
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_same_monster_slug(self):
        self.mon.owner = self.player
        self.mon.slug = "rockat"
        evo = MonsterEvolutionItemModel(monster_slug="rockat")
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_tech_match(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(monster_slug="rockat", tech="ram")
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_traded_match(self):
        self.mon.owner = self.player
        self.mon.traded = True
        evo = MonsterEvolutionItemModel(monster_slug="rockat", traded=True)
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_traded_mismatch(self):
        self.mon.owner = self.player
        self.mon.traded = False
        evo = MonsterEvolutionItemModel(monster_slug="rockat", traded=True)
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_party_match(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(monster_slug="rockat", party=["nut"])
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_party_match_double(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", party=["nut", "rockitten"]
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_party_mismatch(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", party=["agnidon"]
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_taste_cold_match(self):
        self.mon.owner = self.player
        self.mon.taste_cold = "flakey"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", taste_cold="flakey"
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_taste_cold_mismatch(self):
        self.mon.owner = self.player
        self.mon.taste_cold = "mild"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", taste_cold="flakey"
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_taste_warm_match(self):
        self.mon.owner = self.player
        self.mon.taste_warm = "peppy"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", taste_warm="peppy"
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_taste_warm_mismatch(self):
        self.mon.owner = self.player
        self.mon.taste_warm = "peppy"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", taste_warm="salty"
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_stats_match(self):
        self.mon.owner = self.player
        self.mon.hp = 30
        self.mon.melee = 20
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", stats="hp:greater_or_equal:melee"
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_stats_mismatch(self):
        self.mon.owner = self.player
        self.mon.speed = 5
        self.mon.armour = 10
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", stats="speed:greater_or_equal:armour"
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_variables_match(self):
        self.mon.owner = self.player
        self.player.game_variables["var"] = "val"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", variables=[{"var": "val"}]
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_variables_mismatch(self):
        self.mon.owner = self.player
        self.player.game_variables["var"] = "other_val"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", variables=[{"var": "val"}]
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_variables_double_match(self):
        self.mon.owner = self.player
        self.player.game_variables["var1"] = "val"
        self.player.game_variables["var2"] = "val"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", variables=[{"var1": "val"}, {"var2": "val"}]
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_variables_double_mismatch(self):
        self.mon.owner = self.player
        self.player.game_variables["var1"] = "val"
        self.player.game_variables["var2"] = "val"
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat",
            variables=[{"var1": "val"}, {"var2": "other_val"}],
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_steps_match(self):
        self.mon.owner = self.player
        self.mon.steps = 10
        evo = MonsterEvolutionItemModel(monster_slug="rockat", steps=10)
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_steps_mismatch(self):
        self.mon.owner = self.player
        self.mon.steps = 5
        evo = MonsterEvolutionItemModel(monster_slug="rockat", steps=10)
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_bond_match(self):
        self.mon.owner = self.player
        self.mon.bond = 10
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", bond="greater_or_equal:10"
        )
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_bond_mismatch(self):
        self.mon.owner = self.player
        self.mon.bond = 5
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", bond="greater_or_equal:10"
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_item_match(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(
            monster_slug="botbot", item="booster_tech"
        )
        context = {"map_inside": True, "use_item": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_item_mismatch(self):
        self.mon.owner = self.player
        evo = MonsterEvolutionItemModel(
            monster_slug="botbot", item="booster_tech"
        )
        context = {"map_inside": True, "use_item": False}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_element_match(self):
        self.mon.owner = self.player
        self.mon.types = [Element("metal")]
        evo = MonsterEvolutionItemModel(monster_slug="botbot", element="metal")
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_element_mismatch(self):
        self.mon.owner = self.player
        self.mon.types = [Element("metal")]
        evo = MonsterEvolutionItemModel(monster_slug="botbot", element="water")
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))

    def test_moves_match(self):
        self.mon.owner = self.player
        tech = Technique.create("ram")
        self.mon.learn(tech)
        evo = MonsterEvolutionItemModel(monster_slug="rockat", moves=["ram"])
        context = {"map_inside": True}
        self.assertTrue(self.mon.evolution_handler.can_evolve(evo, context))

    def test_moves_mismatch(self):
        self.mon.owner = self.player
        tech = Technique.create("ram")
        self.mon.learn(tech)
        evo = MonsterEvolutionItemModel(
            monster_slug="rockat", moves=["strike"]
        )
        context = {"map_inside": True}
        self.assertFalse(self.mon.evolution_handler.can_evolve(evo, context))
