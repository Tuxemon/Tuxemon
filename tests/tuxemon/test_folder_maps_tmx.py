# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import re
import xml.etree.ElementTree as ET
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.database.runtime import db  # noqa: F401  # side‑effect import
from tuxemon.map.manager import MAP_TYPES
from tuxemon.platform.const.sizes import REGION_KEYS
from tuxemon.script.parser import parse_action_string

# Constants
FOLDER = "maps"
MULTIPLIER = 16
MIN_LAYERS = 4
TMX_TYPES_PREFIXES = ("init", "collision", "event")


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
    region_properties_set = set(REGION_KEYS)
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


@pytest.fixture(scope="module")
def loaded_data():
    folder_path = fetch_asset(FOLDER)
    return load_tmx_files(folder_path)


def test_top_level_properties_map_type(loaded_data):
    for path, root in loaded_data.items():
        prop = root.find("properties")
        if prop is not None:
            assert _is_object_property(
                prop, "map_type", list(MAP_TYPES.keys())
            ), f"Map Type wrong name ({list(MAP_TYPES.keys())})"


def test_object_id(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            object_id = obj.attrib.get("id")
            if object_id and not _is_valid_integer(object_id):
                pytest.fail(f"Invalid id '{object_id}' in object {obj}")


def test_object_id_duplicate(loaded_data):
    for path, root in loaded_data.items():
        seen = set()
        for obj in root.findall(".//objectgroup/object"):
            object_id = obj.attrib.get("id")
            if object_id and _is_valid_integer(object_id):
                if object_id in seen:
                    pytest.fail(f"ID '{object_id}' is a duplicate in {path}")
                seen.add(object_id)


def test_object_types(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            obj_name = obj.attrib.get("type", "")
            if not _is_object_type(obj_name):
                if not obj_name:
                    obj_name = "type:'event' is missing from the object!"
                pytest.fail(obj_name)


def test_object_property_name(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            for prop in obj.findall("properties/property"):
                name = prop.attrib["name"]
                if not _is_valid_property_name(name):
                    pytest.fail(f"Invalid property name '{name}'")

                value = prop.attrib["value"]
                if name.startswith("cond"):
                    if not re.match(r"^(is|not)", value):
                        pytest.fail(
                            f"Invalid property value '{value}' for name '{name}'"
                        )


def test_object_property_name_duplicate(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            seen = set()
            for prop in obj.findall("properties/property"):
                name = prop.attrib["name"]
                if _is_valid_property_name(name):
                    if name in seen:
                        pytest.fail(f"Duplicate property name '{name}'")
                    seen.add(name)


def test_object_property_value_teleport(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            for prop in obj.findall("properties/property"):
                try:
                    action, params = parse_action_string(prop.attrib["value"])
                    if action == "transition_teleport":
                        fetch_asset(FOLDER, params[1])
                except OSError:
                    pytest.fail(f"Map '{params[1]}' does not exist")


def test_object_width(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            width = obj.attrib.get("width")
            if width:
                assert _is_valid_integer(width), f"Invalid width '{width}'"
                assert _is_multiple_of_16(width), (
                    f"Width '{width}' is not a multiple of 16"
                )


def test_object_height(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            height = obj.attrib.get("height")
            if height:
                assert _is_valid_integer(height), f"Invalid height '{height}'"
                assert _is_multiple_of_16(height), (
                    f"Height '{height}' is not a multiple of 16"
                )


def test_object_x(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            x = obj.attrib.get("x")
            if x:
                assert _is_valid_integer(x), f"Invalid x '{x}'"
                assert _is_multiple_of_16(x), (
                    f"X '{x}' is not a multiple of 16"
                )


def test_object_y(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            y = obj.attrib.get("y")
            if y:
                assert _is_valid_integer(y), f"Invalid y '{y}'"
                assert _is_multiple_of_16(y), (
                    f"Y '{y}' is not a multiple of 16"
                )


def test_tileset_source(loaded_data):
    for path, root in loaded_data.items():
        tileset = root.find(".//tileset")
        if tileset is not None and "source" in tileset.attrib:
            tileset_source = tileset.attrib["source"]
            base_path = Path(fetch_asset("gfx"))
            merged_path = (base_path / tileset_source).resolve()
            assert merged_path.is_file(), (
                f"Source '{merged_path}' doesn't exist"
            )


def test_layer_number(loaded_data):
    for path, root in loaded_data.items():
        layers = root.findall(".//layer")
        assert len(layers) >= MIN_LAYERS, (
            f"File must contain at least {MIN_LAYERS} layers."
        )


def test_object_bounds(loaded_data):
    for path, root in loaded_data.items():
        map_width = int(root.attrib["width"]) * int(root.attrib["tilewidth"])
        map_height = int(root.attrib["height"]) * int(
            root.attrib["tileheight"]
        )

        for obj in root.findall(".//object"):
            name = obj.attrib.get("name", "collision")
            x = int(obj.attrib.get("x", 0))
            y = int(obj.attrib.get("y", 0))
            w = int(obj.attrib.get("width", 0))
            h = int(obj.attrib.get("height", 0))

            msg = f"Object '{name}' is out of bounds."
            assert x <= map_width - w, msg
            assert y <= map_height - h, msg
            assert x >= 0, msg
            assert y >= 0, msg


def test_map_attributes_validity(loaded_data):
    for path, root in loaded_data.items():
        for attr in ["width", "height", "tilewidth", "tileheight"]:
            value = root.attrib.get(attr)
            assert value is not None, (
                f"Missing required map attribute: '{attr}'."
            )
            assert _is_valid_integer(value), (
                f"Invalid integer value '{value}' for map attribute '{attr}'."
            )


def test_unique_layer_names(loaded_data):
    for path, root in loaded_data.items():
        names = [
            layer.attrib["name"]
            for layer in root.findall(".//layer")
            if "name" in layer.attrib
        ]
        duplicates = {n for n in names if names.count(n) > 1}
        assert len(duplicates) == 0, (
            f"Duplicate layer names found: {', '.join(sorted(duplicates))}"
        )


def test_object_property_name_duplicate_with_subtest(loaded_data):
    for path, root in loaded_data.items():
        for obj in root.findall(".//object"):
            seen = set()
            for prop in obj.findall("properties/property"):
                name = prop.attrib["name"]
                if name in seen:
                    pytest.fail(
                        f"Duplicate property name '{name}' within the same object."
                    )
                seen.add(name)
