"""
Move the scripts from TMX file to a YAML file

* the YAML file will have same name as map
* the TMX file will have the events, but the data will be removed

Run this script with one or more files as the argument(s).  YAML files will be
generated in the same folder with the same name as the map, and will contain
the event data.

The event data will be removed from the TMX map, but the rects will still be in
the events group.  They can be deleted, if desired.

... at some point I may make it remove the group if no events are in it.

USAGE

python yamlify_map_script.py FILE0 FILE1 FILE2 ...

You can run the script like this:

    python3 scripts/yamlify_map_script.py mods/tuxemon/maps/map.tmx
"""

import logging
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from tuxemon.database.yaml_utils import dump_yaml_io, load_yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def renumber_event(event_node: Element) -> defaultdict[Any, list]:
    groups = (
        ("act", []),
        ("cond", []),
        ("behav", []),
    )

    for node in event_node:
        item = node.attrib["name"], node.attrib["value"]
        for tag, items in groups:
            if item[0].startswith(tag):
                items.append(item)
                break
        else:
            raise ValueError(node.attrib)

    children = defaultdict(list)
    for tag, items in groups:
        items.sort()
        for item in items:
            index, value = item
            children[tag].append(value)

    return children


def extract_events(filename: Path) -> None:
    tree = ET.parse(filename)
    root = tree.getroot()
    yaml_filename = filename.with_suffix(".yaml")

    try:
        yaml_doc = load_yaml(yaml_filename)
    except FileNotFoundError:
        yaml_doc = {"events": {}}

    mapping = (
        ("conditions", "cond"),
        ("actions", "act"),
        ("behav", "behav"),
    )

    tw = int(root.get("tilewidth"))
    th = int(root.get("tileheight"))

    def process_event(obj: Element) -> None:
        event_node = {}

        for names, divisor in [[["x", "width"], tw], [["y", "height"], th]]:
            for name in names:
                value = obj.attrib.get(name)
                if value is not None:
                    event_node[name] = int(value) // divisor

        event_node["height"] = int(obj.attrib.get("height", "1")) // th
        event_node["width"] = int(obj.attrib.get("width", "1")) // tw
        event_node["type"] = obj.attrib.get("type", "event")

        properties = obj.find("properties")
        if properties is not None and len(properties) > 0:
            children = renumber_event(properties)
            for cname, tname in mapping:
                if tname in children:
                    event_node[cname] = children.pop(tname)
            assert not children

        yaml_doc["events"][obj.attrib["name"]] = event_node

    for obj in root.findall(".//object[@type='interact']"):
        process_event(obj)
    for obj in root.findall(".//object[@type='event']"):
        process_event(obj)

    with yaml_filename.open("w", encoding="utf-8") as fp:
        dump_yaml_io(
            fp,
            yaml_doc,
            sort_keys=False,
            default_flow_style=False,
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: python yamlify_map_script.py FILE0 FILE1 FILE2 ...")
        sys.exit(1)

    for filename in sys.argv[1:]:
        extract_events(Path(filename))
