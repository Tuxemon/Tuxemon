# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path
from typing import Any

import pytest
import yaml

ALL_TECHNIQUES = 274
MAX_TECH_ID = 268

SIMPLE_DAMAGE_EFFECT = ("damage", "retaliate", "revenge", "money", "splash")
SIMPLE_HEAL_EFFECT = ("healing", "photogenesis")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TECHNIQUE_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/technique"


def load_technique_data() -> list[dict[str, Any]]:
    data_list = []
    for file in TECHNIQUE_FOLDER.iterdir():
        if file.suffix in (".yaml", ".yml") and file.is_file():
            with file.open("r", encoding="utf-8") as f:
                data_list.append(yaml.safe_load(f))
    return data_list


@pytest.fixture(scope="session")
def data_list():
    return load_technique_data()


def test_nr_jsons(data_list):
    assert len(data_list) == ALL_TECHNIQUES


def test_missing_tech_ids(data_list):
    numbers = [d["tech_id"] for d in data_list if d["tech_id"] > 0]

    all_numbers = set(range(1, MAX_TECH_ID))
    given_numbers = set(numbers)
    missing = all_numbers - given_numbers

    assert not missing, f"Missing tech_ids: {missing}"


def test_duplicate_tech_ids(data_list):
    numbers = [d["tech_id"] for d in data_list if d["tech_id"] > 0]

    seen = set()
    duplicates = set()

    for n in numbers:
        if n in seen:
            duplicates.add(n)
        seen.add(n)

    assert not duplicates, f"Duplicate tech_ids: {duplicates}"


def test_effects_simple_damage_special(data_list):
    errors = []

    for data in data_list:
        slug = data["slug"]
        effects = data["effects"]
        ranges = data["range"]

        if (
            effects
            and effects[0] in SIMPLE_DAMAGE_EFFECT
            and ranges == "special"
        ):
            errors.append(
                f"{slug}: 'special' range cannot be used with {SIMPLE_DAMAGE_EFFECT}"
            )

    assert not errors, "Invalid special-range techniques:\n" + "\n".join(
        errors
    )


def test_effects_simple_damage_power(data_list):
    errors = []

    for data in data_list:
        slug = data["slug"]
        effects = data["effects"]
        power = data["power"]

        if effects and effects[0] in SIMPLE_DAMAGE_EFFECT and power == 0:
            errors.append(f"{slug}: power is 0")

    assert not errors, "Damage techniques must have power > 0:\n" + "\n".join(
        errors
    )


def test_effects_simple_heal_healing_power(data_list):
    errors = []

    for data in data_list:
        slug = data["slug"]
        effects = data["effects"]

        if effects and effects[0] in SIMPLE_HEAL_EFFECT:
            healing_power = data.get("healing_power")
            if healing_power is not None and healing_power == 0:
                errors.append(f"{slug}: healing_power is 0")

    assert not errors, (
        "Healing techniques must have healing_power > 0:\n" + "\n".join(errors)
    )


def test_effects_combinations(data_list):
    forbidden = {
        (
            "damage",
            "healing",
        ): "The 'damage' and 'healing' effects cannot be used together."
    }

    errors = {}

    for data in data_list:
        slug = data["slug"]
        effects = data["effects"]

        if effects:
            for combo, message in forbidden.items():
                if all(effect in effects for effect in combo):
                    errors.setdefault(message, []).append(
                        f"{slug}: effects={effects}"
                    )

    assert not errors, "\n".join(
        f"{msg}\n" + "\n".join(items) for msg, items in errors.items()
    )


def test_effects_give(data_list):
    errors = []

    for data in data_list:
        slug = data["slug"]
        effects = data["effects"]
        potency = data["potency"]

        if effects:
            for effect in effects:
                if effect.get("type") == "give" and potency == 0.0:
                    errors.append(f"{slug}: potency is 0")

    assert not errors, "give-effects require potency > 0:\n" + "\n".join(
        errors
    )
