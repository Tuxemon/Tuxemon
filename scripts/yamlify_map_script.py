"""

Move the scripts from tmx file to a YAML file

* the YAML file will have same name as map
* the TMX map will have the event, but not the script
* events are referenced by name, not id

USAGE

python yamlify_map_script.py FILE0 FILE1 FILE2 ...

"""
import logging
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from itertools import count
import yaml

import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def renumber_event(event_node, sorting_method):
    groups = (
        ("act", list()),
        ("cond", list()),
        ("behav", list()),
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
        items = sorting_method(items)
        num_digits = len(str(len(items) * 10))
        name_template = tag + "{:0%d}" % num_digits

        for i, action in zip(count(10, 10), items):
            name, value = action
            name = name_template.format(i)
            for tag, items in groups:
                if name.startswith(tag):
                    break
            else:
                raise ValueError(tag)
            children[tag].append(value)

    return children


def rewrite_events(filename: str, sorting_method):
    tree = ET.parse(filename)
    root = tree.getroot()
    yaml_filename = filename[:-4] + ".yaml"

    # if there is an existing yaml, try to load it so it is updated instead of replaced
    try:
        # http://yaml.org/faq.html
        with open(yaml_filename) as fp:
            yaml_doc = yaml.load(fp, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        yaml_doc = dict()
        yaml_doc["events"] = dict()

    mapping = (
        ("conditions", "cond"),
        ("actions", "act"),
        ("behav", "behav"),
    )

    tw = int(root.get("tilewidth"))
    th = int(root.get("tileheight"))

    for xml_event_object in root.findall(".//object[@type='event']"):
        properties = xml_event_object.find("properties")
        event_node = dict()
        for names, divisor in [[["x", "width"], tw], [["y", "height"], th]]:
            for name in names:
                value = xml_event_object.attrib.get(name, None)
                if value is not None:
                    event_node[name] = int(value) // divisor
        event_type = xml_event_object.get("type")
        if event_type is not None:
            event_node["type"] = event_type
        if properties:
            xml_event_object.remove(properties)
            children = renumber_event(properties, sorting_method)
            for cname, tname in mapping:
                if tname in children:
                    event_node[cname] = children.pop(tname)
            assert not children
        yaml_doc["events"][xml_event_object.attrib["name"]] = event_node

    with open(yaml_filename, "w") as fp:
        fp.write(yaml.dump(yaml_doc, Dumper=yaml.SafeDumper))

    tree.write(filename, encoding="UTF-8", xml_declaration=True)


def process_tmxmap(filename, sort_method):
    logging.info("processing file %s", filename)
    rewrite_events(filename, sorted)
    # python's xml export changes formatting, so use tiled
    # to export the map again and fix formatting
    tiled_exe = "/home/ltheden/Downloads/Tiled-1.7.0-x86_64.AppImage"
    cmd = "{} --export-map {} {}".format(tiled_exe, filename, filename)
    os.system(cmd)


@click.command()
@click.option("--ascii", "method", flag_value="ascii")
@click.option("--natural", "method", flag_value="natural", default=True)
@click.argument("filename", nargs=-1)
def click_shim(method, filename):
    for fn in filename:
        process_tmxmap(fn, method)


if __name__ == "__main__":
    click_shim()
