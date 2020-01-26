"""
This is used to create the json files for the techniques.
Put the techniques.xlsx file in the scripts folder alongside this.
Call this script from the root folder.
"name_trans.txt" will also be created, which contains the english locale entries, and can
be copy-pasted into en_US.json
"""

from collections import namedtuple
from json import dump
from openpyxl import load_workbook

excel_path = 'scripts/techniques.xlsx'
wb2 = load_workbook(excel_path)
tech_sheet = wb2.get_sheet_by_name('Techs')

DataRow = namedtuple("DataRow", [
    "name",
    "id",
    "element",
    "recharge",
    "accuracy",
    "potency",
    "user_condition",
    "target_condition",
    "animation",
    "animation_target",
    "range",
    "power",
    "healing_power",
    "is_fast",
    "is_area"
])


def create_json(data_row):
    name = data_row.name.lower().replace(" ", "_").replace("-", "_")
    name_trans['technique_%s_name' % name] = data_row.name.strip()
    types = [t.strip().lower() for t in data_row.element.split(",")]
    effects = []
    if data_row.power:
        effects += ["damage"]

    template = {
        "slug": name,
        "use_tech": "combat_used_x",
        "use_success": None,
        "use_failure": "combat_miss",
        "animation": data_row.animation,
        "sfx": "blaster1.ogg",
        "icon": "",
        "accuracy": data_row.accuracy,
        "category": "physical",
        "effects": effects,
        "healing_power": float(data_row.healing_power) if data_row.healing_power else 0,
        "is_area": bool(data_row.is_area),
        "is_fast": bool(data_row.is_fast),
        "potency": data_row.potency,
        "power": float(data_row.power) if data_row.power else 0,
        "range": data_row.range.lower(),
        "recharge": int(data_row.recharge),
        "sort": "damage",
        "target": {
            "enemy monster": 2,
            "enemy team": 0,
            "enemy trainer": 0,
            "own monster": 1,
            "own team": 0,
            "own trainer": 0,
            "item": 0
        },
        "types": types,
    }

    path = "tuxemon/resources/db/technique/%s.json" % name
    with open(path, "w") as f:
        dump(template, f, indent=2, separators=(",", ": "), sort_keys=True)
        f.write("\n")


name_trans = {}

for y in range(2, 6000):
    row = DataRow(*(tech_sheet.cell(row=y, column=x).value for x in range(1, 16)))
    if row.name is None:
        break
    create_json(row)

path = "name_trans.txt"
with open(path, "w") as f:
    dump(name_trans, f, indent=2, separators=(",", ": "), sort_keys=True)
