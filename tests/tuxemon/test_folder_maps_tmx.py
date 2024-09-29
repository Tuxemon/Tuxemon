# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import os
import re
import unittest
import xml.etree.ElementTree as ET
from collections.abc import Generator
from typing import Any

from tuxemon import prepare
from tuxemon.db import MapType
from tuxemon.map_loader import region_properties
from tuxemon.script.parser import parse_action_string

# Constants
FOLDER = "maps"
MULTIPLIER = 16
TMX_TYPES_PREFIXES = ("init", "collision", "event")
EXPECTED_SCENARIOS = ["spyder", "xero", "tobedefined"]


def expand_expected_scenarios() -> None:
    for mod in prepare.CONFIG.mods:
        EXPECTED_SCENARIOS.append(f"{prepare.STARTING_MAP}{mod}")


def get_tmx_files(folder_path: str) -> Generator[str, Any, None]:
    for file in os.listdir(folder_path):
        if file.endswith(".tmx"):
            yield os.path.join(folder_path, file)


def load_tmx_files(folder_path: str) -> dict[str, ET.Element]:
    loaded_data: dict[str, ET.Element] = {}
    for file_path in get_tmx_files(folder_path):
        tree = ET.parse(file_path)
        loaded_data[file_path] = tree.getroot()
    return loaded_data


def to_basename(filepath: str) -> str:
    return os.path.basename(filepath)


def _is_object_property(
    obj: ET.Element, property_element: str, valid_options: list[str]
) -> bool:
    for element in obj.findall("property"):
        if element.attrib["name"] == property_element:
            return element.attrib["value"] in valid_options
    return True


def _is_object_type(obj_name: str) -> bool:
    return obj_name.lower().startswith(TMX_TYPES_PREFIXES)


def _is_valid_integer(value: str) -> bool:
    try:
        int(value)
        return value == str(int(value))
    except ValueError:
        return False


def _is_multiple_of_16(value) -> bool:
    return int(value) % MULTIPLIER == 0


def _is_valid_property_name(name) -> bool:
    region_properties_set = set(region_properties)
    if name in region_properties_set:
        return True
    opt = ("act", "cond", "behav")
    if name.startswith(opt):
        return _is_valid_operand_name(name)
    return False


def _is_valid_operand_name(name) -> bool:
    for prefix in ("act", "cond", "behav"):
        if name.startswith(prefix) and name[len(prefix) :].isdigit():
            return True
    return False


class TestTMXFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.folder_path = prepare.fetch(FOLDER)
        self.loaded_data = load_tmx_files(self.folder_path)
        expand_expected_scenarios()

    def test_top_level_properties_scenario(self) -> None:
        for path, root in self.loaded_data.items():
            prop = root.find("properties")
            if prop is not None:
                self.assertTrue(
                    _is_object_property(prop, "scenario", EXPECTED_SCENARIOS),
                    f"Scenario wrong name {to_basename(path)} ({EXPECTED_SCENARIOS})",
                )

    def test_top_level_properties_map_type(self) -> None:
        for path, root in self.loaded_data.items():
            prop = root.find("properties")
            if prop is not None:
                self.assertTrue(
                    _is_object_property(prop, "map_type", list(MapType)),
                    f"Map Type wrong name {to_basename(path)} ({list(MapType)})",
                )

    def test_object_id(self) -> None:
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                object_id = obj.attrib.get("id")
                if object_id and not _is_valid_integer(object_id):
                    self.fail(
                        f"Invalid id '{object_id}' in object {obj} at {to_basename(path)}"
                    )

    def test_object_id_duplicate(self) -> None:
        object_ids: set[int] = set()
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//objectgroup/object"):
                object_id = obj.attrib.get("id")
                if object_id and not _is_valid_integer(object_id):
                    self.assertNotIn(
                        object_id,
                        object_ids,
                        f"ID '{object_id}' is a duplicate in {to_basename(path)}",
                    )
                    object_ids.add(object_id)

    def test_object_types(self) -> None:
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                obj_name = obj.attrib.get("type", "")
                if not _is_object_type(obj_name):
                    if len(obj_name) == 0:
                        obj_name = "type:'event' is missing from the object!"
                    msg = f"{obj_name} {to_basename(path)}"
                    self.fail(msg)

    def test_object_property_name(self):
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                for prop in obj.findall("properties/property"):
                    name = prop.attrib["name"]
                    if not _is_valid_property_name(name):
                        self.fail(
                            f"Invalid property name '{name}' in object {obj} at {to_basename(path)}"
                        )
                    value = prop.attrib["value"]
                    if name.startswith("cond"):
                        pattern = r"^(is|not)"
                        if not re.match(pattern, value):
                            self.fail(
                                f"Invalid property value '{value}' for name '{name}' in object {obj} at {to_basename(path)}"
                            )

    def test_object_property_name_duplicate(self):
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                property_names = {}
                for prop in obj.findall("properties/property"):
                    if _is_valid_property_name(prop.attrib["name"]):
                        if prop.attrib["name"] in property_names:
                            self.fail(
                                f"Duplicate property name '{prop.attrib['name']}' in object {obj} at {to_basename(path)}"
                            )
                        else:
                            property_names[prop.attrib["name"]] = True

    def test_object_property_value_teleport(self):
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                for prop in obj.findall("properties/property"):
                    action, params = parse_action_string(prop.attrib["value"])
                    if action == "transition_teleport":
                        try:
                            prepare.fetch(FOLDER, params[0])
                        except OSError:
                            self.fail(
                                f"Map '{params[0]}' does not exist in object {obj} at {to_basename(path)}"
                            )

    def test_object_width(self):
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                width = obj.attrib.get("width")
                if width and not _is_valid_integer(width):
                    self.fail(
                        f"Invalid width '{width}' in object {obj} at {to_basename(path)}"
                    )
                if width and not _is_multiple_of_16(width):
                    self.fail(
                        f"Width '{width}' is not a multiple of 16 in object {obj} at {to_basename(path)}"
                    )

    def test_object_height(self):
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                height = obj.attrib.get("height")
                if height and not _is_valid_integer(height):
                    self.fail(
                        f"Invalid height '{height}' in object {obj} at {to_basename(path)}"
                    )
                if height and not _is_multiple_of_16(height):
                    self.fail(
                        f"Height '{height}' is not a multiple of 16 in object {obj} at {to_basename(path)}"
                    )

    def test_object_x(self) -> None:
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                _x = obj.attrib.get("x")
                if _x and not _is_valid_integer(_x):
                    self.fail(
                        f"Invalid x '{_x}' in object {obj} at {to_basename(path)}"
                    )
                if _x and not _is_multiple_of_16(_x):
                    self.fail(
                        f"X '{_x}' is not a multiple of 16 in object {obj} at {to_basename(path)}"
                    )

    def test_object_y(self) -> None:
        for path, root in self.loaded_data.items():
            for obj in root.findall(".//object"):
                _y = obj.attrib.get("y")
                if _y and not _is_valid_integer(_y):
                    self.fail(
                        f"Invalid y '{_y}' in object {obj} at {to_basename(path)}"
                    )
                if _y and not _is_multiple_of_16(_y):
                    self.fail(
                        f"Y '{_y}' is not a multiple of 16 in object {obj} at {to_basename(path)}"
                    )

    def test_tileset_source(self) -> None:
        for path, root in self.loaded_data.items():
            tileset_element = root.find(".//tileset")
            if (
                tileset_element is not None
                and "source" in tileset_element.attrib
            ):
                tileset_source = tileset_element.attrib["source"]
                base_path = prepare.fetch("gfx")
                merged_path = os.path.realpath(
                    os.path.join(base_path, tileset_source)
                )
                msg = (
                    f"Source '{merged_path}' doesn't exist {to_basename(path)}"
                )
                self.assertTrue(os.path.isfile(merged_path), msg)

    def test_object_bounds(self) -> None:
        for path, root in self.loaded_data.items():
            map_width = int(root.attrib["width"]) * int(
                root.attrib["tilewidth"]
            )
            map_height = int(root.attrib["height"]) * int(
                root.attrib["tileheight"]
            )

            for obj in root.findall(".//object"):
                obj_name = obj.attrib.get("name", "collision")
                obj_x = int(obj.attrib.get("x", 0))
                obj_y = int(obj.attrib.get("y", 0))
                obj_width = int(obj.attrib.get("width", 0))
                obj_height = int(obj.attrib.get("height", 0))

                self.assertLessEqual(
                    obj_x,
                    map_width - obj_width,
                    f"Object '{obj_name}' at ({obj_x}, {obj_y}) with size ({obj_width}, {obj_height}) is out of bounds in map '{to_basename(path)}' with size ({map_width}, {map_height})",
                )
                self.assertLessEqual(
                    obj_y,
                    map_height - obj_height,
                    f"Object '{obj_name}' at ({obj_x}, {obj_y}) with size ({obj_width}, {obj_height}) is out of bounds in map '{to_basename(path)}' with size ({map_width}, {map_height})",
                )
                self.assertGreaterEqual(
                    obj_x,
                    0,
                    f"Object '{obj_name}' at ({obj_x}, {obj_y}) with size ({obj_width}, {obj_height}) is out of bounds in map '{to_basename(path)}' with size ({map_width}, {map_height})",
                )
                self.assertGreaterEqual(
                    obj_y,
                    0,
                    f"Object '{obj_name}' at ({obj_x}, {obj_y}) with size ({obj_width}, {obj_height}) is out of bounds in map '{to_basename(path)}' with size ({map_width}, {map_height})",
                )
