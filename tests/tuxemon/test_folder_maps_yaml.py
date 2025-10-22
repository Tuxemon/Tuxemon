# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from collections.abc import Generator
from pathlib import Path
from typing import Any

import yaml

from tuxemon import prepare
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.db import db
from tuxemon.script.parser import parse_action_string

EXPECTED_SCENARIOS = ["spyder", "xero", "tobedefined", "eclipse"]
FOLDER = "maps"
EVENTS_KEY = "events"
COLLISION_KEY = "collisions"
MAX_LENGTH_NAME = 50
YAML_ATTR = [
    "actions",
    "conditions",
    "behav",
    "type",
    "x",
    "y",
    "width",
    "height",
]
YAML_TYPES = ["init", "collision", "event"]


def expand_expected_scenarios() -> None:
    for mod in prepare.CONFIG.mods:
        map: str = db.mod_metadata.require_mod_attribute(mod, "starting_map")
        EXPECTED_SCENARIOS.append(map.removesuffix(".tmx"))


def get_yaml_files(folder_path: Path) -> Generator[Path, Any, None]:
    for file in folder_path.iterdir():
        if file.suffix == ".yaml" and file.is_file():
            yield file


def load_yaml_files(folder_path: str) -> dict[Path, dict]:
    loaded_data = {}
    for file_path in get_yaml_files(Path(folder_path)):
        try:
            with file_path.open("r") as f:
                loaded_data[file_path] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to load YAML file: {file_path}") from e
    return loaded_data


class TestYAMLFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder_path = fetch_asset(FOLDER)
        cls.loaded_data = load_yaml_files(cls.folder_path)
        expand_expected_scenarios()

    def test_yaml_event_name_length(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_name in data[EVENTS_KEY].keys():
                    with self.subTest(event_name=event_name):
                        self.assertLessEqual(
                            len(event_name),
                            MAX_LENGTH_NAME,
                            f"Event name exceeds {MAX_LENGTH_NAME} characters.",
                        )

    def test_yaml_event_labels(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    for name in event_data.keys():
                        with self.subTest(attribute_name=name):
                            self.assertIn(
                                name,
                                YAML_ATTR,
                                f"Attribute '{name}' is not in the list of allowed attributes.",
                            )

    def test_yaml_event_type(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    with self.subTest(event_data=event_data):
                        self.assertIn(
                            event_data["type"],
                            YAML_TYPES,
                            f"Event type '{event_data['type']}' is not in the list of allowed types.",
                        )

    def test_yaml_event_coordinates_and_dimensions(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    with self.subTest(event_data=event_data):
                        # Test 'x'
                        if "x" in event_data:
                            self.assertIsInstance(
                                event_data["x"],
                                int,
                                "Value of 'x' should be an integer.",
                            )
                        # Test 'y'
                        if "y" in event_data:
                            self.assertIsInstance(
                                event_data["y"],
                                int,
                                "Value of 'y' should be an integer.",
                            )
                        # Test 'width'
                        if "width" in event_data:
                            self.assertIsInstance(
                                event_data["width"],
                                int,
                                "Value of 'width' should be an integer.",
                            )
                        # Test 'height'
                        if "height" in event_data:
                            self.assertIsInstance(
                                event_data["height"],
                                int,
                                "Value of 'height' should be an integer.",
                            )

    def test_actions_structure(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    if "actions" in event_data:
                        for action in event_data["actions"]:
                            with self.subTest(action=action):
                                self.assertIsInstance(
                                    action,
                                    str,
                                    "Action in event should be a string.",
                                )

    def test_actions_teleport(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    if "actions" in event_data:
                        for action in event_data["actions"]:
                            command, params = parse_action_string(action)
                            if command == "transition_teleport":
                                with self.subTest(action=action):
                                    try:
                                        fetch_asset(FOLDER, params[0])
                                    except OSError:
                                        self.fail(
                                            f"Map '{params[0]}' does not exist."
                                        )

    def test_conditions_structure(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    if "conditions" in event_data:
                        for condition in event_data["conditions"]:
                            with self.subTest(condition=condition):
                                self.assertIsInstance(
                                    condition,
                                    str,
                                    "Condition in event should be a string.",
                                )

    def test_conditions_operator(self):
        for path, data in self.loaded_data.items():
            with self.subTest(file=path.name):
                for event_data in data[EVENTS_KEY].values():
                    if "conditions" in event_data:
                        for condition in event_data["conditions"]:
                            with self.subTest(condition=condition):
                                self.assertTrue(
                                    condition.lower().startswith(
                                        ("is ", "not ")
                                    ),
                                    "Condition should start with 'is ' or 'not '.",
                                )

    def test_collision_attributes(self):
        for path, data in self.loaded_data.items():
            if COLLISION_KEY in data:
                with self.subTest(file=path.name):
                    for collision in data[COLLISION_KEY]:
                        self.assertIsInstance(
                            collision,
                            dict,
                            "Collision entry must be a dictionary.",
                        )
                        required_attrs = ["height", "type", "width", "x", "y"]
                        for attr in required_attrs:
                            self.assertIn(
                                attr,
                                collision,
                                f"Collision object is missing required attribute '{attr}'.",
                            )

    def test_collision_attribute_values(self):
        for path, data in self.loaded_data.items():
            if COLLISION_KEY in data:
                with self.subTest(file=path.name):
                    for collision in data[COLLISION_KEY]:
                        # Check type
                        self.assertEqual(
                            collision.get("type"),
                            "collision",
                            "The 'type' for a collision object must be 'collision'.",
                        )
                        # Check integer attributes
                        integer_attrs = ["height", "width", "x", "y"]
                        for attr in integer_attrs:
                            if attr in collision:
                                self.assertIsInstance(
                                    collision[attr],
                                    int,
                                    f"The value for '{attr}' must be an integer.",
                                )

    def test_collision_no_event_data(self):
        for path, data in self.loaded_data.items():
            if COLLISION_KEY in data:
                with self.subTest(file=path.name):
                    for collision in data[COLLISION_KEY]:
                        self.assertNotIn(
                            "actions",
                            collision,
                            "Collision object should not have an 'actions' key.",
                        )
                        self.assertNotIn(
                            "conditions",
                            collision,
                            "Collision object should not have a 'conditions' key.",
                        )
