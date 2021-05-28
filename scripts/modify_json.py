""" modify_json

This script allows the user to add or change a certain value to all json files included in a folder.
This is done by taking a folder filled with json files, and creating a new folder at a target
location filled with the new json files. The changes or not directly done to the original folder
to ensure that we do not lose any data.

All the json files are converted and handled as dictionaries.

The script is run through the command line and has 4 parameters:

input_folder: The folder that contains the json files that you want to add or change values
output_folder: The folder that the changed json files will appear
variable_name: The name of the variable you want to introduce or change
variable_value: The value of the variable tou want to introduce or change

E.g if we want to introduce the new catch_rate and give it the value 125 to all files i will run
python modify_json input_file output_file catch_rate 125
The new json files will be located at the output file

-GDMarkou
"""

import os
import json
import sys


def json_to_dict(json_file):
    """Open a json file and loads it as a python dictionary

    Parameters
    ----------
    json_file: file .json

    Returns
    --------
    json_dict: dict
    """
    with open(json_file) as f:
        json_dict = json.load(f)
        return json_dict


def save_dict(json_dict, output_file):
    """Writes the new value of the json file to the output_folder

   Parameters
   ----------
   json_dict: dict
   output_file: file .json
   """
    with open(output_file, 'w') as fp:
        json.dump(json_dict, fp, indent=4, sort_keys=False, default=str)


def modify_json(input_folder, output_folder, variable_name, variable_value):
    """Add or change a certain value to all json files included in a folder

    Parameters
    ----------
    input_folder: String
        location of the folder containing the json files
    output_folder: String
        location of the folder we want to create the new json files
    variable_name: String
        The name of the variable we want to create
    variable_value: Float
        The value of the variable we want to create
    """
    # if the output_folder does not exist it is created via code
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    jsons = os.listdir(input_folder)

    for jfile in jsons:
        jfile_path = os.path.join(input_folder, jfile)
        jdict = json_to_dict(jfile_path)
        jdict[variable_name] = variable_value
        save_path = os.path.join(output_folder, jfile)
        save_dict(jdict, save_path)


if __name__ == '__main__':
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    variable_name = sys.argv[3]
    variable_value = float(sys.argv[4])
    modify_json(input_folder, output_folder, variable_name, variable_value)
