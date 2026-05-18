# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path
from typing import Any

import pytest
import yaml

ALL_MONSTERS = 411
MAX_TXMN_ID = 393
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MONSTER_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/monster"


def load_monster_data() -> list[dict[str, Any]]:
    data_list = []
    for file in MONSTER_FOLDER.iterdir():
        if file.suffix in (".yaml", ".yml") and file.is_file():
            with file.open("r", encoding="utf-8") as f:
                data_list.append(yaml.safe_load(f))
    return data_list


@pytest.fixture(scope="session")
def data_list():
    return load_monster_data()


def test_nr_jsons(data_list):
    assert len(data_list) == ALL_MONSTERS


def test_missing_txmn_ids(data_list):
    numbers = [d["txmn_id"] for d in data_list if d["txmn_id"] > 0]

    all_numbers = set(range(1, MAX_TXMN_ID))
    given_numbers = set(numbers)
    missing = all_numbers - given_numbers

    assert not missing, f"Missing txmn_ids: {missing}"


def test_duplicate_txmn_ids(data_list):
    numbers = [d["txmn_id"] for d in data_list if d["txmn_id"] > 0]

    seen = set()
    duplicates = set()

    for n in numbers:
        if n in seen:
            duplicates.add(n)
        seen.add(n)

    assert not duplicates, f"Duplicate txmn_ids: {duplicates}"


def test_history_structure_and_links(data_list):
    errors = []

    all_slugs = {d["slug"] for d in data_list}
    stage_order = {"basic": 0, "stage1": 1, "stage2": 2}

    slug_to_data = {d["slug"]: d for d in data_list}

    for data in data_list:
        slug = data["slug"]
        stage = data["stage"]
        history = data.get("history", [])
        evolutions = data.get("evolutions", [])

        # 1. Self-entry must exist
        if not any(h["slug"] == slug for h in history):
            errors.append(f"{slug} missing self-entry in history")

        # 2. All referenced slugs must exist
        for h in history:
            refs = h.get("evolves_from", []) + h.get("evolves_into", [])
            for ref in refs:
                if ref not in all_slugs:
                    errors.append(f"{slug} history references unknown '{ref}'")

        # 3. Evolution slugs must appear in history
        for evo in evolutions:
            evo_slug = evo["monster_slug"]
            if not any(h["slug"] == evo_slug for h in history):
                errors.append(f"{slug} history missing evolution '{evo_slug}'")

        # 4. Standalone monsters must have only self-entry
        if stage == "standalone":
            if len(history) != 1 or history[0]["slug"] != slug:
                errors.append(
                    f"{slug} is standalone but has extra history entries"
                )

        # 5. Stage progression check (informational only)
        for h in history:
            target = slug_to_data.get(h["slug"])
            if target and h["slug"] != slug:
                from_stage = stage_order.get(stage, -1)
                to_stage = stage_order.get(target["stage"], -1)
                if to_stage <= from_stage:
                    pass  # allowed, but could be logged

    assert not errors, "History model validation failed:\n" + "\n".join(errors)


def test_moveset_level_learned_evolution_at_level(data_list):
    START_LEVEL = 1
    errors = []

    for data in data_list:
        slug = data["slug"]
        evolutions = data["evolutions"]
        moveset = data["moveset"]

        if moveset and evolutions:
            at_levels = {
                evo.get("at_level")
                for evo in evolutions
                if evo.get("at_level") is not None
            }

            levels = [m["level_learned"] for m in moveset] + list(at_levels)

            duplicates = [
                lvl
                for lvl in set(levels)
                if levels.count(lvl) > 1 and lvl != START_LEVEL
            ]

            if duplicates:
                errors.append(f"{slug}: duplicate levels {duplicates}")

    assert not errors, "Moveset/evolution level conflicts:\n" + "\n".join(
        errors
    )


def test_moveset_level_sequence(data_list):
    RANGE = 34
    START = 1
    INTERVAL = 3

    valid_levels = {START + INTERVAL * i for i in range(RANGE)}
    errors = []

    for data in data_list:
        slug = data["slug"]
        moveset = data["moveset"]

        if moveset:
            levels = [m["level_learned"] for m in moveset]
            invalid = [lvl for lvl in levels if lvl not in valid_levels]

            if invalid:
                errors.append(f"{slug}: invalid levels {invalid}")

    assert not errors, (
        "Invalid moveset levels (must be 1,4,7,10,...):\n" + "\n".join(errors)
    )
