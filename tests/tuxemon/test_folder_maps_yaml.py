# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.database.runtime import db  # noqa: F401  # side‑effect import
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.script.parser import parse_action_string

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


def get_yaml_files(folder_path: Path) -> Generator[Path, Any, None]:
    for file in folder_path.iterdir():
        if file.suffix == ".yaml" and file.is_file():
            yield file


def load_yaml_files(folder_path: str) -> dict[Path, dict]:
    loaded_data: dict[Path, dict] = {}

    for file_path in get_yaml_files(Path(folder_path)):
        try:
            loaded_data[file_path] = load_yaml(file_path)
        except Exception as e:
            raise ValueError(f"Failed to load YAML file: {file_path}") from e

    return loaded_data


@pytest.fixture(scope="module")
def loaded_data():
    folder_path = fetch_asset(FOLDER)
    return load_yaml_files(folder_path)


def test_yaml_event_name_length(loaded_data):
    for path, data in loaded_data.items():
        for event_name in data[EVENTS_KEY].keys():
            assert len(event_name) <= MAX_LENGTH_NAME, (
                f"Event name exceeds {MAX_LENGTH_NAME} characters."
            )


def test_yaml_event_labels(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            for name in event_data.keys():
                assert name in YAML_ATTR, (
                    f"Attribute '{name}' is not in the list of allowed attributes."
                )


def test_yaml_event_type(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            assert event_data["type"] in YAML_TYPES, (
                f"Event type '{event_data['type']}' is not in the list of allowed types."
            )


def test_yaml_event_coordinates_and_dimensions(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            for key in ("x", "y", "width", "height"):
                if key in event_data:
                    assert isinstance(event_data[key], int), (
                        f"Value of '{key}' should be an integer."
                    )


def test_actions_structure(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            if "actions" in event_data:
                for action in event_data["actions"]:
                    assert isinstance(action, str), (
                        "Action in event should be a string."
                    )


def test_actions_teleport(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            if "actions" in event_data:
                for action in event_data["actions"]:
                    command, params = parse_action_string(action)
                    if command == "transition_teleport":
                        try:
                            fetch_asset(FOLDER, params[1])
                        except OSError:
                            pytest.fail(f"Map '{params[1]}' does not exist.")


def test_conditions_structure(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            if "conditions" in event_data:
                for condition in event_data["conditions"]:
                    assert isinstance(condition, str), (
                        "Condition in event should be a string."
                    )


def test_conditions_operator(loaded_data):
    for path, data in loaded_data.items():
        for event_data in data[EVENTS_KEY].values():
            if "conditions" in event_data:
                for condition in event_data["conditions"]:
                    assert condition.lower().startswith(("is ", "not ")), (
                        "Condition should start with 'is ' or 'not '."
                    )


def test_collision_attributes(loaded_data):
    for path, data in loaded_data.items():
        if COLLISION_KEY in data:
            for collision in data[COLLISION_KEY]:
                assert isinstance(collision, dict), (
                    "Collision entry must be a dictionary."
                )
                for attr in ["height", "type", "width", "x", "y"]:
                    assert attr in collision, (
                        f"Collision object is missing required attribute '{attr}'."
                    )


def test_collision_attribute_values(loaded_data):
    for path, data in loaded_data.items():
        if COLLISION_KEY in data:
            for collision in data[COLLISION_KEY]:
                assert collision.get("type") == "collision", (
                    "The 'type' for a collision object must be 'collision'."
                )
                for attr in ["height", "width", "x", "y"]:
                    if attr in collision:
                        assert isinstance(collision[attr], int), (
                            f"The value for '{attr}' must be an integer."
                        )


def test_collision_no_event_data(loaded_data):
    for path, data in loaded_data.items():
        if COLLISION_KEY in data:
            for collision in data[COLLISION_KEY]:
                assert "actions" not in collision, (
                    "Collision object should not have an 'actions' key."
                )
                assert "conditions" not in collision, (
                    "Collision object should not have a 'conditions' key."
                )
