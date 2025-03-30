# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import os
import unittest
from collections.abc import Generator
from typing import Any

import yaml

from tuxemon import prepare
from tuxemon.script.parser import parse_action_string

EXPECTED_SCENARIOS = ["spyder", "xero", "tobedefined"]
FOLDER = "maps"
EVENTS_KEY = "events"
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
        EXPECTED_SCENARIOS.append(f"{prepare.STARTING_MAP}{mod}")


def get_yaml_files(folder_path: str) -> Generator[str, Any, None]:
    for file in os.listdir(folder_path):
        if file.endswith(".yaml"):
            yield os.path.join(folder_path, file)


def load_yaml_files(folder_path: str) -> dict[str, dict]:
    loaded_data = {}
    for file_path in get_yaml_files(folder_path):
        try:
            with open(file_path, "r") as f:
                loaded_data[file_path] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to load YAML file: {file_path}") from e
    return loaded_data


class TestYAMLFiles(unittest.TestCase):
    def setUp(self):
        self.folder_path = prepare.fetch(FOLDER)
        self.loaded_data = load_yaml_files(self.folder_path)
        expand_expected_scenarios()

    def test_yaml_event_name_length(self):
        for path, data in self.loaded_data.items():
            for event_name in data[EVENTS_KEY].keys():
                self.assertLessEqual(
                    len(event_name),
                    MAX_LENGTH_NAME,
                    f"Event name {event_name} exceeds {MAX_LENGTH_NAME} characters: {os.path.basename(path)}",
                )

    def test_yaml_event_labels(self):
        for path, data in self.loaded_data.items():
            for _, event_data in data[EVENTS_KEY].items():
                for name in event_data.keys():
                    self.assertIn(
                        name,
                        YAML_ATTR,
                        f"Event name {name} isn't among {YAML_ATTR}: {os.path.basename(path)}",
                    )

    def test_yaml_event_type(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                self.assertIn(
                    event_data["type"],
                    YAML_TYPES,
                    f"Event type {event_data['type']} isn't among {YAML_TYPES}: {os.path.basename(path)}",
                )

    def test_yaml_event_x_coordinate(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "x" in event_data:
                    self.assertIsInstance(
                        event_data["x"],
                        int,
                        f"Value of 'x' should be an integer: {os.path.basename(path)}",
                    )

    def test_yaml_event_y_coordinate(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "y" in event_data:
                    self.assertIsInstance(
                        event_data["y"],
                        int,
                        f"Value of 'y' should be an integer: {os.path.basename(path)}",
                    )

    def test_yaml_event_width(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "width" in event_data:
                    self.assertIsInstance(
                        event_data["width"],
                        int,
                        f"Value of 'width' should be an integer: {os.path.basename(path)}",
                    )

    def test_yaml_event_height(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "height" in event_data:
                    self.assertIsInstance(
                        event_data["height"],
                        int,
                        f"Value of 'height' should be an integer: {os.path.basename(path)}",
                    )

    def test_actions_structure(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "actions" in event_data:
                    for action in event_data["actions"]:
                        self.assertIsInstance(
                            action,
                            str,
                            f"Action in event should be a string: {os.path.basename(path)}",
                        )

    def test_actions_teleport(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "actions" in event_data:
                    for action in event_data["actions"]:
                        command, params = parse_action_string(action)
                        if command == "transition_teleport":
                            try:
                                prepare.fetch(FOLDER, params[0])
                            except OSError:
                                self.fail(
                                    f"Map '{params[0]}' does not exist in object {action} at {os.path.basename(path)}"
                                )

    def test_conditions_structure(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "conditions" in event_data:
                    for condition in event_data["conditions"]:
                        self.assertIsInstance(
                            condition,
                            str,
                            f"Condition in event should be a string: {os.path.basename(path)}",
                        )

    def test_conditions_operator(self):
        for path, data in self.loaded_data.items():
            for event_data in data[EVENTS_KEY].values():
                if "conditions" in event_data:
                    for condition in event_data["conditions"]:
                        self.assertTrue(
                            condition.lower().startswith(("is ", "not ")),
                            f"Condition '{condition}' should start with 'is' or 'not': {os.path.basename(path)}",
                        )
