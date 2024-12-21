# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import json
import os
import unittest
from typing import Any

from tuxemon import prepare

ALL_MONSTERS: int = 377
MAX_TXMN_ID: int = 359


def process_json_data(directory: str) -> list[dict[str, Any]]:
    data_list = []
    directory = f"{prepare.fetch('db')}/{directory}/"
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data_list.append(json.load(f))
    return data_list


def get_history(
    data_list: list[dict[str, Any]], slug: str
) -> list[dict[str, Any]]:
    for data in data_list:
        if data["slug"] == slug:
            return data["history"]
    return []


class TestJSONProcessing(unittest.TestCase):
    def setUp(self) -> None:
        sample_data = "monster"
        self.data_list = process_json_data(sample_data)

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

    def test_history_current_slug(self) -> None:
        missing_monsters = []
        for data in self.data_list:
            slug = data["slug"]
            history = data["history"]
            if history:
                for element in history:
                    if element["mon_slug"] == "slug":
                        missing_monsters.append(
                            f"{slug}'s history cannot contain {slug} ({history})"
                        )
        if missing_monsters:
            print(
                "The following monsters have history that contains themselves:"
            )
            for monster in missing_monsters:
                print(monster)
            self.fail("History cannot contain slug.")

    def test_history_evolution(self) -> None:
        missing_monsters = []
        for data in self.data_list:
            original = data["slug"]
            history = data["history"]
            evolutions = data["evolutions"]
            if evolutions:
                for evolution in evolutions:
                    slug = evolution["monster_slug"]
                    if history and slug not in [
                        h["mon_slug"] for h in history
                    ]:
                        missing_monsters.append(
                            f"{original}'s history must contain {evolution['monster_slug']} ({history})"
                        )
        if missing_monsters:
            print(
                "The following monsters have history that doesn't contain their evolution:"
            )
            for monster in missing_monsters:
                print(monster)
            self.fail("History must contain evolution slug.")

    def test_history_standalone(self) -> None:
        for data in self.data_list:
            stage = data["stage"]
            if stage == "standalone":
                self.assertEqual(
                    len(data["history"]),
                    0,
                    f"{data['slug']} is standalone, it has no history",
                )

    def test_history_standalone(self) -> None:
        for data in self.data_list:
            stage = data["stage"]
            if stage == "standalone":
                self.assertEqual(
                    len(data["history"]),
                    0,
                    f"{data['slug']} is standalone, it has no history",
                )

    def test_stage_basic(self) -> None:
        for data in self.data_list:
            evo_stages = [h["evo_stage"] for h in data["history"]]
            if data["stage"] == "basic" and data["evolutions"]:
                self.assertIn(
                    "stage1",
                    evo_stages,
                    f"{data['slug']}'s history lacks the 'evo_stage':'stage1' ({data['history']})",
                )
            if data["stage"] == "basic" and not data["evolutions"]:
                self.fail(
                    f"{data['slug']} is basic, but there are no evolutions ({data['evolutions']})"
                )

    def test_stage_stage1(self) -> None:
        for data in self.data_list:
            evo_stages = [h["evo_stage"] for h in data["history"]]
            if data["stage"] == "stage1":
                self.assertIn(
                    "basic",
                    evo_stages,
                    f"{data['slug']}'s history lacks the 'evo_stage':'basic' ({data['history']})",
                )
                if data["evolutions"]:
                    self.assertIn(
                        "stage2",
                        evo_stages,
                        f"{data['slug']}'s history lacks the 'evo_stage':'stage2' ({data['history']})",
                    )
                names = [h["mon_slug"] for h in data["history"]]
                for name in names:
                    history = get_history(self.data_list, name)
                    history_names = [h["mon_slug"] for h in history]
                    self.assertIn(data["slug"], history_names)

    def test_stage_stage2(self) -> None:
        for data in self.data_list:
            evo_stages = [h["evo_stage"] for h in data["history"]]
            if data["stage"] == "stage2":
                self.assertIn(
                    "basic",
                    evo_stages,
                    f"{data['slug']}'s history lacks the 'evo_stage':'basic' ({data['history']})",
                )
                self.assertIn(
                    "stage1",
                    evo_stages,
                    f"{data['slug']}'s history lacks the 'evo_stage':'stage1' ({data['history']})",
                )
                names = [h["mon_slug"] for h in data["history"]]
                for name in names:
                    history = get_history(self.data_list, name)
                    history_names = [h["mon_slug"] for h in history]
                    self.assertIn(data["slug"], history_names)

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
