# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.db import Modifier
from tuxemon.element import Element, ElementTypesHandler
from tuxemon.modifiers import ModifiersHandler
from tuxemon.monster import Monster


class TestModifiersHandler(unittest.TestCase):

    def setUp(self):
        self.fire = MagicMock(spec=Element)
        self.fire.name = "fire"
        self.water = MagicMock(spec=Element)
        self.water.name = "water"
        self.grass = MagicMock(spec=Element)
        self.grass.name = "grass"
        self.aether = MagicMock(spec=Element)
        self.aether.name = "aether"
        self.monster = MagicMock(spec=Monster)
        self.monster.types = MagicMock(spec=ElementTypesHandler)
        self.monster.types.current = []
        self.monster.name = ""

    def test_init(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.assertEqual(handler.list_modifiers(), modifiers)
        self.assertIn("type", handler._modifiers)
        self.assertEqual(len(handler._modifiers["type"]), 1)

    def test_get_modifiers(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.assertEqual(handler.get_modifiers("type"), modifiers)

    def test_has_modifier(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.assertTrue(handler.has_modifier("type"))
        self.assertFalse(handler.has_modifier("nonexistent"))

    def test_update_modifier(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        handler.update_modifier("type", ["water"], 0.8)
        updated_modifiers = handler.get_modifiers("type")

        self.assertEqual(updated_modifiers[0].values, ["water"])
        self.assertEqual(updated_modifiers[0].multiplier, 0.8)
        for m in handler.get_modifiers("type"):
            self.assertEqual(m.values, ["water"])
            self.assertEqual(m.multiplier, 0.8)

    def test_remove_modifier(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        handler.remove_modifier("type")
        self.assertFalse(handler.has_modifier("type"))

    def test_add_modifier(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        new_modifier = Modifier(
            attribute="type", values=["water"], multiplier=0.8
        )
        handler.add_modifier(new_modifier)
        self.assertEqual(len(handler._modifiers["type"]), 2)

    def test_weakest_link(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire]
        self.assertEqual(handler.weakest_link(self.monster), 0.5)
        self.monster.types.current = [self.water]
        self.assertEqual(handler.weakest_link(self.monster), 1.0)

    def test_strongest_link(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire]
        self.assertEqual(handler.strongest_link(self.monster), 0.5)
        self.monster.types.current = [self.water]
        self.assertEqual(handler.strongest_link(self.monster), 1.0)

    def test_cumulative_damage(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire]
        self.assertEqual(handler.cumulative_damage(self.monster), 0.5)
        self.monster.types.current = [self.water]
        self.assertEqual(handler.cumulative_damage(self.monster), 1.0)

    def test_average_damage(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire]
        self.assertEqual(handler.average_damage(self.monster), 0.5)
        self.monster.types.current = [self.water]
        self.assertEqual(handler.average_damage(self.monster), 1.0)

    def test_first_applicable_damage(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5)
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire]
        self.assertEqual(handler.first_applicable_damage(self.monster), 0.5)
        self.monster.types.current = [self.water]
        self.assertEqual(handler.first_applicable_damage(self.monster), 1.0)

    def test_edge_cases(self):
        handler = ModifiersHandler([])
        self.monster.types.current = [self.fire]
        self.assertEqual(handler.weakest_link(self.monster), 1.0)
        self.assertEqual(handler.strongest_link(self.monster), 1.0)
        self.assertEqual(handler.cumulative_damage(self.monster), 1.0)
        self.assertEqual(handler.average_damage(self.monster), 1.0)
        self.assertEqual(handler.first_applicable_damage(self.monster), 1.0)

    def test_multiple_modifiers(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire, self.water]
        self.assertEqual(handler.weakest_link(self.monster), 0.5)
        self.assertEqual(handler.strongest_link(self.monster), 0.8)
        self.assertEqual(handler.cumulative_damage(self.monster), 0.4)
        self.assertEqual(handler.average_damage(self.monster), 0.65)
        self.assertEqual(handler.first_applicable_damage(self.monster), 0.5)

    def test_tag_modifiers(self):
        modifiers = [
            Modifier(attribute="tag", values=["tag1"], multiplier=0.5),
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.tags = ["tag1"]
        self.assertEqual(handler.weakest_link(self.monster), 0.5)
        self.assertEqual(handler.strongest_link(self.monster), 0.5)
        self.assertEqual(handler.cumulative_damage(self.monster), 0.5)
        self.assertEqual(handler.average_damage(self.monster), 0.5)
        self.assertEqual(handler.first_applicable_damage(self.monster), 0.5)

    def test_invalid_attribute(self):
        modifiers = [
            Modifier(attribute="invalid", values=["fire"], multiplier=0.5),
        ]
        handler = ModifiersHandler(modifiers)
        self.monster.types.current = [self.fire]
        with self.assertRaises(ValueError):
            handler.weakest_link(self.monster)
        with self.assertRaises(ValueError):
            handler.strongest_link(self.monster)
        with self.assertRaises(ValueError):
            handler.cumulative_damage(self.monster)
        with self.assertRaises(ValueError):
            handler.average_damage(self.monster)
        with self.assertRaises(ValueError):
            handler.first_applicable_damage(self.monster)

    def test_list_modifiers(self):
        modifiers = [
            Modifier(attribute="type", values=["fire"], multiplier=0.5),
            Modifier(attribute="type", values=["water"], multiplier=0.8),
        ]
        handler = ModifiersHandler(modifiers)
        self.assertEqual(handler.list_modifiers(), modifiers)
