# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import re
import unittest
import xml.etree.ElementTree as ET
from collections.abc import Generator
from pathlib import Path
from typing import Any

from tuxemon import prepare
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.db import db
from tuxemon.map.map_manager import map_types_list
from tuxemon.script.parser import parse_action_string

# Constants
FOLDER = "maps"
MULTIPLIER = 16
MIN_LAYERS = 4
TMX_TYPES_PREFIXES = ("init", "collision", "event")
EXPECTED_SCENARIOS = ["spyder", "xero", "tobedefined"]


def expand_expected_scenarios() -> None:
    for mod in prepare.CONFIG.mods:
        map: str = db.mod_metadata.require_mod_attribute(mod, "starting_map")
        EXPECTED_SCENARIOS.append(map.removesuffix(".tmx"))


def get_tmx_files(folder_path: Path) -> Generator[Path, Any, None]:
    for file in folder_path.iterdir():
        if file.suffix == ".tmx" and file.is_file():
            yield file


def load_tmx_files(folder_path: str) -> dict[str, ET.Element]:
    loaded_data: dict[Path, ET.Element] = {}
    for file_path in get_tmx_files(Path(folder_path)):
        tree = ET.parse(file_path)
        loaded_data[file_path] = tree.getroot()
    return loaded_data


def to_basename(filepath: str) -> str:
    return Path(filepath).name


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
    region_properties_set = set(prepare.REGION_KEYS)
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
    @classmethod
    def setUpClass(cls):
        cls.folder_path = fetch_asset(FOLDER)
        cls.loaded_data = load_tmx_files(cls.folder_path)
        expand_expected_scenarios()

    def test_top_level_properties_scenario(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                prop = root.find("properties")
                if prop is not None:
                    self.assertTrue(
                        _is_object_property(
                            prop, "scenario", EXPECTED_SCENARIOS
                        ),
                        f"Scenario wrong name ({EXPECTED_SCENARIOS})",
                    )

    def test_top_level_properties_map_type(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                prop = root.find("properties")
                if prop is not None:
                    self.assertTrue(
                        _is_object_property(prop, "map_type", map_types_list),
                        f"Map Type wrong name ({map_types_list})",
                    )

    def test_object_id(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        object_id = obj.attrib.get("id")
                        if object_id and not _is_valid_integer(object_id):
                            self.fail(
                                f"Invalid id '{object_id}' in object {obj}"
                            )

    def test_object_id_duplicate(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                object_ids: set[str] = set()
                for obj in root.findall(".//objectgroup/object"):
                    object_id = obj.attrib.get("id")
                    if object_id and _is_valid_integer(object_id):
                        if object_id in object_ids:
                            self.fail(f"ID '{object_id}' is a duplicate")
                        object_ids.add(object_id)

    def test_object_types(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        obj_name = obj.attrib.get("type", "")
                        if not _is_object_type(obj_name):
                            if not obj_name:
                                obj_name = (
                                    "type:'event' is missing from the object!"
                                )
                            self.fail(f"{obj_name}")

    def test_object_property_name(self):
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        for prop in obj.findall("properties/property"):
                            with self.subTest(property_element=prop):
                                name = prop.attrib["name"]
                                if not _is_valid_property_name(name):
                                    self.fail(
                                        f"Invalid property name '{name}'"
                                    )
                                value = prop.attrib["value"]
                                if name.startswith("cond"):
                                    pattern = r"^(is|not)"
                                    if not re.match(pattern, value):
                                        self.fail(
                                            f"Invalid property value '{value}' for name '{name}'"
                                        )

    def test_object_property_name_duplicate(self):
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        property_names = {}
                        for prop in obj.findall("properties/property"):
                            name = prop.attrib["name"]
                            if _is_valid_property_name(name):
                                if name in property_names:
                                    self.fail(
                                        f"Duplicate property name '{name}'"
                                    )
                                else:
                                    property_names[name] = True

    def test_object_property_value_teleport(self):
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        for prop in obj.findall("properties/property"):
                            with self.subTest(property_element=prop):
                                try:
                                    action, params = parse_action_string(
                                        prop.attrib["value"]
                                    )
                                    if action == "transition_teleport":
                                        fetch_asset(FOLDER, params[0])
                                except OSError:
                                    self.fail(
                                        f"Map '{params[0]}' does not exist"
                                    )

    def test_object_width(self):
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        width = obj.attrib.get("width")
                        if width:
                            if not _is_valid_integer(width):
                                self.fail(f"Invalid width '{width}'")
                            if not _is_multiple_of_16(width):
                                self.fail(
                                    f"Width '{width}' is not a multiple of 16"
                                )

    def test_object_height(self):
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        height = obj.attrib.get("height")
                        if height:
                            if not _is_valid_integer(height):
                                self.fail(f"Invalid height '{height}'")
                            if not _is_multiple_of_16(height):
                                self.fail(
                                    f"Height '{height}' is not a multiple of 16"
                                )

    def test_object_x(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        _x = obj.attrib.get("x")
                        if _x:
                            if not _is_valid_integer(_x):
                                self.fail(f"Invalid x '{_x}'")
                            if not _is_multiple_of_16(_x):
                                self.fail(f"X '{_x}' is not a multiple of 16")

    def test_object_y(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        _y = obj.attrib.get("y")
                        if _y:
                            if not _is_valid_integer(_y):
                                self.fail(f"Invalid y '{_y}'")
                            if not _is_multiple_of_16(_y):
                                self.fail(f"Y '{_y}' is not a multiple of 16")

    def test_tileset_source(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                tileset_element = root.find(".//tileset")
                if (
                    tileset_element is not None
                    and "source" in tileset_element.attrib
                ):
                    tileset_source = tileset_element.attrib["source"]
                    base_path = Path(fetch_asset("gfx"))
                    merged_path = (base_path / tileset_source).resolve()
                    msg = f"Source '{merged_path}' doesn't exist"
                    self.assertTrue(merged_path.is_file(), msg)

    def test_layer_number(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                layer_elements = root.findall(".//layer")
                self.assertGreaterEqual(
                    len(layer_elements),
                    MIN_LAYERS,
                    f"File must contain at least {MIN_LAYERS} layers.",
                )

    def test_object_bounds(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                map_width = int(root.attrib["width"]) * int(
                    root.attrib["tilewidth"]
                )
                map_height = int(root.attrib["height"]) * int(
                    root.attrib["tileheight"]
                )

                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        obj_name = obj.attrib.get("name", "collision")
                        obj_x = int(obj.attrib.get("x", 0))
                        obj_y = int(obj.attrib.get("y", 0))
                        obj_width = int(obj.attrib.get("width", 0))
                        obj_height = int(obj.attrib.get("height", 0))

                        msg = f"Object '{obj_name}' is out of bounds."
                        self.assertLessEqual(obj_x, map_width - obj_width, msg)
                        self.assertLessEqual(
                            obj_y, map_height - obj_height, msg
                        )
                        self.assertGreaterEqual(obj_x, 0, msg)
                        self.assertGreaterEqual(obj_y, 0, msg)

    def test_map_attributes_validity(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                map_attributes = ["width", "height", "tilewidth", "tileheight"]
                for attr in map_attributes:
                    value = root.attrib.get(attr)
                    self.assertIsNotNone(
                        value, f"Missing required map attribute: '{attr}'."
                    )
                    self.assertTrue(
                        _is_valid_integer(value),
                        f"Invalid integer value '{value}' for map attribute '{attr}'.",
                    )

    def test_unique_layer_names(self) -> None:
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                layer_names = [
                    layer.attrib["name"]
                    for layer in root.findall(".//layer")
                    if "name" in layer.attrib
                ]
                duplicates = {
                    name for name in layer_names if layer_names.count(name) > 1
                }
                self.assertEqual(
                    len(duplicates),
                    0,
                    f"Duplicate layer names found: {', '.join(sorted(duplicates))}",
                )

    def test_object_property_name_duplicate_with_subtest(self):
        for path, root in self.loaded_data.items():
            with self.subTest(file=to_basename(path)):
                for obj in root.findall(".//object"):
                    with self.subTest(object_element=obj):
                        property_names = set()
                        for prop in obj.findall("properties/property"):
                            name = prop.attrib["name"]
                            self.assertNotIn(
                                name,
                                property_names,
                                f"Duplicate property name '{name}' within the same object.",
                            )
                            property_names.add(name)
