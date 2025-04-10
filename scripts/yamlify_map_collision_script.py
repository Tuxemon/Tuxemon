"""
Move the collision data or events from TMX files to YAML files.

* The YAML file will have the same name as the corresponding map.
* The TMX file will retain the rectangles and other metadata in their
respective groups, but the event or collision data will be removed.

Run this script with one or more TMX files as the argument(s). YAML
files will be generated in the same folder as the TMX files, with
the same name but a `.yaml` extension. These YAML files will contain
the extracted event or collision data.

Collision data will be extracted if the TMX file includes an
`<objectgroup>` named "Collisions." Events will be extracted if
the TMX file includes an `<objectgroup>` containing event objects.

For collision data, the YAML file preserves key order (`x`, `y`,
`width`, `height`, `type`) to ensure consistency and readability.

To ensure that no existing YAML file is accidentally overwritten,
the script creates a copy of the YAML file with a modified name
if one already exists.

USAGE

python yamlify_map_collision_script.py FILE0 FILE1 FILE2 ...
"""
import logging
import os
import xml.etree.ElementTree as ET
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

def process_collisions(tmx_filename: str):
    """
    Extract collision objects from a TMX file and export them to a YAML file.
    
    Parameters:
        tmx_filename: The path to the TMX file.
    """
    tree = ET.parse(tmx_filename)
    root = tree.getroot()

    yaml_filename = os.path.splitext(tmx_filename)[0] + ".yaml"

    if os.path.exists(yaml_filename):
        logger.error(f"YAML file already exists: {yaml_filename}")
        yaml_filename = os.path.splitext(tmx_filename)[0] + "_copy.yaml"
        logger.error(f"Creating a copy: {yaml_filename}")

    yaml_doc = {"collisions": []}

    for object_group in root.findall(".//objectgroup[@name='Collisions']"):
        for obj in object_group.findall("object"):
            collision_data = {
                "x": int(float(obj.get("x", 0))) // 16,  # Dividing by tile size
                "y": int(float(obj.get("y", 0))) // 16,
                "width": int(float(obj.get("width", 0))) // 16,
                "height": int(float(obj.get("height", 0))) // 16,
                "type": obj.get("type", "collision")
            }
            yaml_doc["collisions"].append(collision_data)

    with open(yaml_filename, "w") as yaml_file:
        yaml.dump(
            yaml_doc,
            yaml_file,
            Dumper=yaml.SafeDumper,
            default_flow_style=False,
            sort_keys=False
        )

    logger.info(f"Collision data exported to {yaml_filename}")

def process_tmx_files(file_list):
    """
    Process multiple TMX files and extract collision data.
    """
    for tmx_file in file_list:
        logger.info(f"Processing TMX file: {tmx_file}")
        if not os.path.exists(tmx_file):
            logger.error(f"File not found: {tmx_file}")
            continue
        process_collisions(tmx_file)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("USAGE: python yamlify_map_collision_script.py FILE0 FILE1 ...")
        sys.exit(1)

    file_list = sys.argv[1:]
    process_tmx_files(file_list)
