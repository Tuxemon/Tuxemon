"""

Sort and renumber map event actions and conditions

* Sorts actions before conditions
* Renumber items by 10s; 10, 20, 30, 40, etc


USAGE

python renumber_events.py [--ascii/--natural] FILE0 FILE1 FILE2 ...

Natural sort ordering is default.  Use ASCII for fixing old maps.

"""
import logging
import os
import xml.etree.ElementTree as ET
from itertools import count

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

    children = list()
    for tag, items in groups:
        items = sorting_method(items)
        num_digits = len(str(len(items) * 10))
        name_template = tag + "{:0%d}" % num_digits

        for i, action in zip(count(10, 10), items):
            name, value = action
            name = name_template.format(i)
            child = ET.SubElement(event_node, "property", attrib={"name": name, "value": value})
            children.append(child)

    return children


def rewrite_events(filename, sorting_method):
    tree = ET.parse(filename)
    root = tree.getroot()

    for parent in root.findall(".//object[@type='event']/properties"):
        children = renumber_event(parent, sorting_method)
        parent.clear()
        for child in children:
            parent.append(child)

    tree.write(filename, encoding="UTF-8", xml_declaration=True)


def process_tmxmap(filename, sort_method):
    logging.info("processing file %s", filename)
    rewrite_events(filename, sorted)
    # python's xml export changes formatting, so use tiled
    # to export the map again and fix formatting
    tiled_exe = "/home/ltheden/Downloads/Tiled-1.3.2-x86_64.AppImage"
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
