# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import json
import unittest
from pathlib import Path
from typing import Any

ALL_MONSTERS: int = 411
MAX_TXMN_ID: int = 393
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MONSTER_FOLDER = PROJECT_ROOT / "mods/tuxemon/db/monster"


def process_json_data() -> list[dict[str, Any]]:
    data_list = []
    for file in MONSTER_FOLDER.iterdir():
        if file.suffix == ".json" and file.is_file():
            with file.open("r") as f:
                data_list.append(json.load(f))
    return data_list


class TestJSONProcessing(unittest.TestCase):
    def setUp(self) -> None:
        self.data_list = process_json_data()

    def test_nr_jsons(self) -> None:
        self.assertEqual(len(self.data_list), ALL_MONSTERS)

    def test_missing_txmn_ids(self) -> None:
        numbers = []
        for data in self.data_list:
            txmn_id = data["txmn_id"]
            if txmn_id > 0:
                numbers.append(txmn_id)

        all_numbers = set(range(1, MAX_TXMN_ID))
        given_numbers = set(numbers)
        missing = all_numbers - given_numbers
        if missing:
            self.fail(f"There are missing txmn_ids: {missing}")

    def test_duplicate_txmn_ids(self) -> None:
        numbers = []
        for data in self.data_list:
            txmn_id = data["txmn_id"]
            if txmn_id > 0:
                numbers.append(txmn_id)

        duplicates = []
        counts = [0] * (max(numbers) + 1)
        for num in numbers:
            counts[num] += 1
            if counts[num] > 1:
                duplicates.append(num)
        if duplicates:
            self.fail(f"There are duplicates txmn_ids: {duplicates}")

    def test_history_structure_and_links(self) -> None:
        errors = []

        all_slugs = {data["slug"] for data in self.data_list}
        stage_order = {"basic": 0, "stage1": 1, "stage2": 2}

        for data in self.data_list:
            slug = data["slug"]
            stage = data["stage"]
            history = data.get("history", [])
            evolutions = data.get("evolutions", [])

            # 1. Self-entry must exist
            if not any(h["slug"] == slug for h in history):
                errors.append(f"{slug} is missing self-entry in history")

            # 2. All referenced slugs must exist
            for h in history:
                for ref in h.get("evolves_from", []) + h.get(
                    "evolves_into", []
                ):
                    if ref not in all_slugs:
                        errors.append(
                            f"{slug}'s history references unknown monster '{ref}'"
                        )

            # 3. Evolution slugs must appear in history
            for evo in evolutions:
                evo_slug = evo["monster_slug"]
                if not any(h["slug"] == evo_slug for h in history):
                    errors.append(
                        f"{slug}'s history missing evolution '{evo_slug}'"
                    )

            # 4. Standalone monsters should only have self-entry
            if stage == "standalone":
                if len(history) != 1 or history[0]["slug"] != slug:
                    errors.append(
                        f"{slug} is standalone but has non-self history entries"
                    )

            # 5. Stage progression check (informational only)
            # Optional: warn if links point to lower stages, but don't fail
            for h in history:
                target = next(
                    (d for d in self.data_list if d["slug"] == h["slug"]), None
                )
                if target and h["slug"] != slug:
                    from_stage = stage_order.get(stage, -1)
                    to_stage = stage_order.get(target["stage"], -1)
                    if to_stage <= from_stage:
                        # This is now allowed, but you can log it if needed
                        pass  # or log as a warning

        if errors:
            print("\n History validation errors:")
            for error in errors:
                print(" -", error)
            self.fail("History model validation failed.")

    def test_moveset_level_learned_evolution_at_level(self) -> None:
        START_LEVEL = 1
        errors = []
        for data in self.data_list:
            slug = data["slug"]
            evolutions = data["evolutions"]
            moveset = data["moveset"]
            if moveset and evolutions:
                at_levels = set(
                    evolution.get("at_level")
                    for evolution in evolutions
                    if evolution.get("at_level") is not None
                )
                levels = [move["level_learned"] for move in moveset] + list(
                    at_levels
                )
                similar_levels = [
                    level
                    for level in set(levels)
                    if levels.count(level) > 1 and level != START_LEVEL
                ]
                if similar_levels:
                    errors.append(
                        f"Similar levels found in {slug}: {similar_levels}"
                    )
        if errors:
            print("The following monsters:")
            for error in errors:
                print(error)
            self.fail(
                f"Levels must be different, only exception lv {START_LEVEL} starting move."
            )

    def test_moveset_level_sequence(self) -> None:
        RANGE: int = 34  # more or less between 1 and 100
        START: int = 1  # starting level
        INTERVAL: int = 3  # each 3 levels
        errors = []
        for data in self.data_list:
            slug = data["slug"]
            moveset = data["moveset"]
            if moveset:
                levels = [move["level_learned"] for move in moveset]
                sequence_levels = [START + INTERVAL * i for i in range(RANGE)]
                invalid_levels = [
                    level for level in levels if level not in sequence_levels
                ]
                if invalid_levels:
                    errors.append(
                        f"Invalid levels found in {slug}: {invalid_levels}"
                    )
        if errors:
            print("The following monsters:")
            for error in errors:
                print(error)
            self.fail(
                "Levels must be in the sequence 1, 4, 7, 10, 13, 16, etc."
            )
