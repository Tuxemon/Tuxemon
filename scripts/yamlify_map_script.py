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
"""

import logging
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict
from xml.etree.ElementTree import Element

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def renumber_event(event_node: Element) -> DefaultDict[Any, list]:
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


def rewrite_events(filename: Path) -> None:
    def do_the_thing() -> None:
        properties = xml_event_object.find("properties")
        event_node = {}
        for names, divisor in [[["x", "width"], tw], [["y", "height"], th]]:
            for name in names:
                value = xml_event_object.attrib.get(name, None)
                if value is not None:
                    event_node[name] = int(value) // divisor
        event_type = xml_event_object.get("type")
        if event_type not in [None, "event"]:
            event_node["type"] = event_type
        if properties is not None and len(properties) > 0:
            xml_event_object.remove(properties)
            children = renumber_event(properties)
            for cname, tname in mapping:
                if tname in children:
                    event_node[cname] = children.pop(tname)
            assert not children
        yaml_doc["events"][xml_event_object.attrib["name"]] = event_node

    tree = ET.parse(filename)
    root = tree.getroot()
    yaml_filename = filename.with_suffix(".yaml")

    try:
        with yaml_filename.open() as fp:
            yaml_doc = yaml.load(fp, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        yaml_doc = {"events": {}}

    mapping = (
        ("conditions", "cond"),
        ("actions", "act"),
        ("behav", "behav"),
    )

    tw = int(root.get("tilewidth"))
    th = int(root.get("tileheight"))

    for xml_event_object in root.findall(".//object[@type='interact']"):
        do_the_thing()
    for xml_event_object in root.findall(".//object[@type='event']"):
        do_the_thing()

    with yaml_filename.open("w") as fp:
        yaml.dump(yaml_doc, fp, Dumper=yaml.SafeDumper)

    tree.write(filename, encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: python yamlify_map_script.py FILE0 FILE1 FILE2 ...")
        sys.exit(1)

    for filename in sys.argv[1:]:
        rewrite_events(Path(filename))
