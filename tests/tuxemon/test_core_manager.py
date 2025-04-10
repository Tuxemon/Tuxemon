# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.core.core_manager import (
    ConditionManager,
    CoreManager,
    EffectManager,
)
from tuxemon.db import CommonCondition, CommonEffect
from tuxemon.plugin import PluginObject


class TestCoreManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = self.temp_dir.name
        self.category = "category"
        self.plugin_interface = MagicMock(spec=PluginObject)
        self.manager = CoreManager(
            self.plugin_interface, self.path, self.category
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("tuxemon.plugin.load_plugins")
    def test_load_plugins(self, mock_load_plugins):
        mock_load_plugins.return_value = {"TestPlugin": MagicMock()}
        self.manager.load_plugins(
            self.plugin_interface, self.path, self.category
        )
        self.assertIn("TestPlugin", self.manager.classes)

    @patch("importlib.import_module")
    def test_load_plugin_success(self, mock_import_module):
        mock_import_module.return_value = MagicMock(TestPlugin=MagicMock())
        self.manager.load_plugin("TestPlugin")
        self.assertIn("TestPlugin", self.manager.classes)

    @patch("importlib.import_module")
    def test_load_plugin_failure(self, mock_import_module):
        mock_import_module.side_effect = ImportError
        with self.assertLogs("tuxemon", level="ERROR"):
            self.manager.load_plugin("NonExistentPlugin")

    def test_unload_plugin(self):
        self.manager.classes["TestPlugin"] = MagicMock()
        self.manager.unload_plugin("TestPlugin")
        self.assertNotIn("TestPlugin", self.manager.classes)

    def test_parse_object_effect(self):
        effect_instance = MagicMock(spec=PluginObject)
        self.manager.classes = {
            "effect_type": MagicMock(return_value=effect_instance)
        }
        raw_effects = [CommonEffect(type="effect_type", parameters=["param"])]
        parsed_effects = self.manager.parse_object_effect(raw_effects)
        self.assertIn(effect_instance, parsed_effects)

    def test_parse_object_condition(self):
        condition_instance = MagicMock(spec=PluginObject)
        self.manager.classes = {
            "condition_type": MagicMock(return_value=condition_instance)
        }
        raw_conditions = [
            CommonCondition(
                type="condition_type", parameters=["param"], operator="is"
            )
        ]
        parsed_conditions = self.manager.parse_object_condition(raw_conditions)
        self.assertIn(condition_instance, parsed_conditions)


class TestEffectManager(unittest.TestCase):
    def setUp(self):
        self.effect_class = MagicMock(spec=PluginObject)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = self.temp_dir.name
        self.category = "effects"
        self.manager = EffectManager(
            self.effect_class, self.path, self.category
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_effects(self):
        effect_instance = MagicMock(spec=PluginObject)
        self.manager.classes = {
            "effect_type": MagicMock(return_value=effect_instance)
        }
        raw_effects = [CommonEffect(type="effect_type", parameters=["param"])]
        parsed_effects = self.manager.parse_effects(raw_effects)
        self.assertIn(effect_instance, parsed_effects)


class TestConditionManager(unittest.TestCase):
    def setUp(self):
        self.condition_class = MagicMock(spec=PluginObject)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = self.temp_dir.name
        self.category = "conditions"
        self.manager = ConditionManager(
            self.condition_class, self.path, self.category
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_conditions(self):
        condition_instance = MagicMock(spec=PluginObject)
        self.manager.classes = {
            "condition_type": MagicMock(return_value=condition_instance)
        }
        raw_conditions = [
            CommonCondition(
                type="condition_type", parameters=["param"], operator="is"
            )
        ]
        parsed_conditions = self.manager.parse_conditions(raw_conditions)
        self.assertIn(condition_instance, parsed_conditions)
