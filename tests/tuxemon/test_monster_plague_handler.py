# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.db import PlagueType
from tuxemon.monster_dir.plague import (
    MonsterPlagueHandler,
    PlagueData,
    config_plagues,
)


class TestPlagueHandlerCore(unittest.TestCase):

    def setUp(self):
        self.plague_data = {
            "plague1": PlagueData(spreadness=0.1),
            "plague2": PlagueData(spreadness=0.2),
        }
        config_plagues.update(self.plague_data)
        self.handler = MonsterPlagueHandler()

    def test_init(self):
        self.assertEqual(self.handler.current_plagues, {})

    def test_infect(self):
        self.handler.infect("plague1")
        self.assertIn("plague1", self.handler.current_plagues)
        self.assertEqual(
            self.handler.get_plague_type("plague1"), PlagueType.infected
        )

    def test_inoculate(self):
        self.handler.inoculate("plague1")
        self.assertIn("plague1", self.handler.current_plagues)
        self.assertEqual(
            self.handler.get_plague_type("plague1"), PlagueType.inoculated
        )

    def test_remove_plague(self):
        self.handler.infect("plague1")
        self.handler.remove_plague("plague1")
        self.assertNotIn("plague1", self.handler.current_plagues)

    def test_clear_plagues(self):
        self.handler.infect("plague1")
        self.handler.inoculate("plague2")
        self.handler.clear_plagues()
        self.assertEqual(self.handler.current_plagues, {})

    def test_has_plague(self):
        self.assertFalse(self.handler.has_plague("plague1"))
        self.handler.infect("plague1")
        self.assertTrue(self.handler.has_plague("plague1"))

    def test_get_plague_type(self):
        self.handler.infect("plague1")
        self.assertEqual(
            self.handler.get_plague_type("plague1"), PlagueType.infected
        )
        self.assertIsNone(
            self.handler.get_plague_type("plague2")
        )  # not yet infected or inoculated

    def test_is_infected(self):
        self.assertFalse(self.handler.is_infected())
        self.handler.infect("plague1")
        self.assertTrue(self.handler.is_infected())

    def test_is_infected_with(self):
        self.handler.infect("plague1")
        self.assertTrue(self.handler.is_infected_with("plague1"))
        self.assertFalse(self.handler.is_infected_with("plague2"))

    def test_is_inoculated_against(self):
        self.handler.inoculate("plague1")
        self.assertTrue(self.handler.is_inoculated_against("plague1"))
        self.assertFalse(self.handler.is_inoculated_against("plague2"))

    def test_get_infected_slugs(self):
        self.handler.infect("plague1")
        self.handler.inoculate("plague2")
        self.assertEqual(self.handler.get_infected_slugs(), ["plague1"])


class DummyMonster:
    def __init__(
        self,
        name,
        type_slugs,
        shape_slug,
        weight,
        height,
        status_slug=None,
        plague_data=None,
        held_item=None,
    ):
        self.name = name
        self.types = MagicMock()
        self.types.get_type_slugs = MagicMock(return_value=type_slugs)
        self.shape = MagicMock()
        self.shape.slug = shape_slug
        self.weight = weight
        self.height = height
        self.status = MagicMock()
        self.status.get_current_status = MagicMock(
            return_value=MagicMock(slug=status_slug) if status_slug else None
        )
        self.held_item = held_item or MagicMock()
        self.held_item.get_item = MagicMock(return_value=None)
        self.plague = MonsterPlagueHandler(plague_data=plague_data or {})


class TestMonsterPlagueInteraction(unittest.TestCase):

    def setUp(self):
        self.plague_data = {
            "test_plague": PlagueData(
                spreadness=1.0,
                type_weights={"wood": 0.6, "poison": 0.4},
                shape_weights={"brute": 0.7, "humanoid": 0.3},
                resistance_modifiers={
                    "types": {"fire": 0.5},
                    "shapes": {"flier": 0.6},
                    "statuses": {"flying": 0.3},
                },
                weight_range=(10.0, 200.0),
                height_range=(0.5, 2.0),
            )
        }
        config_plagues.update(self.plague_data)

    def test_can_be_infected_by_excluded_by_type_weight(self):
        monster = DummyMonster("FireBrute", ["fire"], "brute", 100.0, 1.5)
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertFalse(result)

    def test_can_be_infected_by_excluded_by_shape_weight(self):
        monster = DummyMonster("woodflier", ["wood"], "flier", 100.0, 1.5)
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertFalse(result)

    def test_can_be_infected_by_excluded_by_weight_range(self):
        monster = DummyMonster("Tinywood", ["wood"], "brute", 5.0, 1.5)
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertFalse(result)

    def test_can_be_infected_by_excluded_by_height_range(self):
        monster = DummyMonster("Tallwood", ["wood"], "brute", 100.0, 3.0)
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertFalse(result)

    @patch("random.random", return_value=0.999)
    def test_can_be_infected_by_with_resistance(self, mock_random):
        monster = DummyMonster(
            "Fireflier", ["fire"], "flier", 100.0, 1.5, "flying"
        )
        self.plague_data["test_plague"].type_weights = {"fire": 1.0}
        self.plague_data["test_plague"].shape_weights = {"flier": 1.0}
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertFalse(result)

    def test_can_be_infected_by_with_no_weights_defined(self):
        plague = PlagueData(spreadness=1.0)
        config_plagues["simple_plague"] = plague
        monster = DummyMonster("AnyMonster", ["ghost"], "slimy", 100.0, 1.5)
        result = monster.plague.can_be_infected_by(monster, "simple_plague")
        self.assertTrue(result)

    @patch("random.random", return_value=0.0)
    def test_can_be_infected_by_when_already_infected_simple(
        self, mock_random
    ):
        monster = DummyMonster("woodBrute", ["wood"], "brute", 100.0, 1.5)
        monster.plague.infect("test_plague")
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertTrue(result)

    @patch("random.random", return_value=0.0)
    def test_can_be_infected_by_when_inoculated(self, _):
        monster = DummyMonster(
            "BugBrute",
            ["bug"],
            "brute",
            100.0,
            1.5,
            "sleeping",
            self.plague_data,
        )
        monster.plague.inoculate("test_plague")
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertFalse(result)

    @patch("random.random", return_value=0.0)
    def test_can_be_infected_by_when_already_infected(self, _):
        monster = DummyMonster(
            "woodBrute",
            ["wood"],
            "brute",
            100.0,
            1.5,
            "sleeping",
            self.plague_data,
        )
        monster.plague.infect("test_plague")
        result = monster.plague.can_be_infected_by(monster, "test_plague")
        self.assertTrue(result)

    def test_try_inoculate_success(self):
        inoc_plague = PlagueData(
            spreadness=0.1,
            inoculation={
                "eligible_types": ["bug"],
                "eligible_shapes": ["humanoid"],
            },
        )
        config_plagues["inoc_plague"] = inoc_plague
        monster = DummyMonster(
            "BugHumanoid",
            ["bug"],
            "humanoid",
            50.0,
            1.0,
            plague_data={"inoc_plague": inoc_plague},
        )
        result = monster.plague.try_inoculate(monster, "inoc_plague")
        self.assertTrue(result)
        self.assertTrue(monster.plague.is_inoculated_against("inoc_plague"))

    def test_try_inoculate_ineligible_type(self):
        inoc_plague = PlagueData(
            spreadness=0.1,
            inoculation={
                "eligible_types": ["bug"],
            },
        )
        config_plagues["inoc_plague"] = inoc_plague
        monster = DummyMonster(
            "FireMonster",
            ["fire"],
            "humanoid",
            50.0,
            1.0,
            plague_data={"inoc_plague": inoc_plague},
        )
        result = monster.plague.try_inoculate(monster, "inoc_plague")
        self.assertFalse(result)

    def test_try_inoculate_ineligible_shape(self):
        inoc_plague = PlagueData(
            spreadness=0.1,
            inoculation={
                "eligible_shapes": ["humanoid"],
            },
        )
        config_plagues["inoc_plague"] = inoc_plague
        monster = DummyMonster(
            "BugBrute",
            ["bug"],
            "brute",
            50.0,
            1.0,
            plague_data={"inoc_plague": inoc_plague},
        )
        result = monster.plague.try_inoculate(monster, "inoc_plague")
        self.assertFalse(result)

    def test_try_inoculate_missing_required_item(self):
        inoc_plague = PlagueData(
            spreadness=0.1,
            inoculation={
                "required_held_item": "antidote",
            },
        )
        config_plagues["inoc_plague"] = inoc_plague
        monster = DummyMonster(
            "BugHumanoid",
            ["bug"],
            "humanoid",
            50.0,
            1.0,
            plague_data={"inoc_plague": inoc_plague},
        )
        monster.held_item.get_item = MagicMock(return_value=None)
        result = monster.plague.try_inoculate(monster, "inoc_plague")
        self.assertFalse(result)

    def test_try_inoculate_with_required_item(self):
        inoc_plague = PlagueData(
            spreadness=0.1,
            inoculation={
                "required_held_item": "antidote",
            },
        )
        config_plagues["inoc_plague"] = inoc_plague
        item = MagicMock()
        item.slug = "antidote"
        monster = DummyMonster(
            "BugHumanoid",
            ["bug"],
            "humanoid",
            50.0,
            1.0,
            plague_data={"inoc_plague": inoc_plague},
        )
        monster.held_item.get_item = MagicMock(return_value=item)
        result = monster.plague.try_inoculate(monster, "inoc_plague")
        self.assertTrue(result)
        self.assertTrue(monster.plague.is_inoculated_against("inoc_plague"))
