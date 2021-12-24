"""

Snap collisions and events to the tile grid

EXAMPLES:

    preview changes:
    python3 scripts/snap_map.py mods/tuxemon/maps/taba_town.tmx

    write changes
    python3 -w scripts/snap_map.py mods/tuxemon/maps/taba_town.tmx

    many files:
    python3 scripts/snap_map.py mods/tuxemon/maps/*tmx

"""
import xml.etree.ElementTree as ET

import click


def snap(attrib, name, interval):
    """Snap value, return True if changed"""
    try:
        original = attrib[name]
        modified = int(round(float(attrib[name]) / interval) * interval)
        modified = str(modified)
        if modified != original:
            attrib[name] = modified
            return True
        return False
    except KeyError:
        pass


def snap_objects(tree):
    root = tree.getroot()
    tw = int(root.attrib["tilewidth"])
    th = int(root.attrib["tileheight"])
    values = (("x", th), ("y", th), ("width", tw), ("height", th))
    changed = False
    for obj in tree.findall("./objectgroup/object"):
        attrib = obj.attrib
        for name, interval in values:
            if snap(attrib, name, interval):
                changed = True
    return changed


@click.command()
@click.option("--write", "-w", is_flag=True, help="write the changes back to the file")
@click.argument("filename", nargs=-1)
def click_shim(filename, write):
    """

    Move all events and collisions in a file to align with the tile grid

    Can accept multiple filenames

    """
    for filepath in filename:
        tree = ET.parse(filepath)
        changed = snap_objects(tree)
        if changed:
            print(f"{filepath} will be changed")
            if write:
                print(f"writing changes to {filepath}...")
                tree.write(
                    filepath,
                    encoding="UTF-8",
                    default_namespace=None,
                    xml_declaration=True,
                    short_empty_elements=True,
                )


if __name__ == "__main__":
    click_shim()
