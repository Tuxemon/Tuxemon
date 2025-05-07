# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from typing import Any

from tuxemon.state import StateBuilder


class MockState:
    def __init__(self, name: str, level: int, metadata: dict[str, Any] = None):
        self.name = name
        self.level = level
        self.metadata = metadata or {}


class TestStateBuilder(unittest.TestCase):
    def setUp(self):
        self.state_class = MockState
        self.builder = StateBuilder(self.state_class)

    def test_build_state_with_attributes(self):
        state = (
            self.builder.add_attribute("name", "TestState")
            .add_attribute("level", 3)
            .add_attribute("metadata", {"key": "value"})
            .build()
        )
        self.assertEqual(state.name, "TestState")
        self.assertEqual(state.level, 3)
        self.assertEqual(state.metadata, {"key": "value"})

    def test_build_state_without_optional_attributes(self):
        state = (
            self.builder.add_attribute("name", "StateWithoutMetadata")
            .add_attribute("level", 1)
            .build()
        )
        self.assertEqual(state.name, "StateWithoutMetadata")
        self.assertEqual(state.level, 1)
        self.assertEqual(state.metadata, {})

    def test_builder_chaining(self):
        self.builder.add_attribute("name", "ChainTest").add_attribute(
            "level", 10
        )
        state = self.builder.build()
        self.assertEqual(state.name, "ChainTest")
        self.assertEqual(state.level, 10)

    def test_overwrite_existing_attribute(self):
        self.builder.add_attribute("name", "InitialName")
        self.builder.add_attribute("name", "OverwrittenName")
        state = self.builder.add_attribute("level", 5).build()
        self.assertEqual(state.name, "OverwrittenName")
        self.assertEqual(state.level, 5)

    def test_build_without_required_attributes(self):
        with self.assertRaises(TypeError):
            self.builder.add_attribute("level", 2).build()

    def test_empty_builder(self):
        with self.assertRaises(TypeError):
            self.builder.build()

    def test_reset_builder(self):
        state1 = (
            self.builder.add_attribute("name", "FirstState")
            .add_attribute("level", 1)
            .build()
        )
        self.assertEqual(state1.name, "FirstState")
        self.assertEqual(state1.level, 1)

        self.builder.attributes.clear()

        state2 = (
            self.builder.add_attribute("name", "SecondState")
            .add_attribute("level", 2)
            .build()
        )
        self.assertEqual(state2.name, "SecondState")
        self.assertEqual(state2.level, 2)
