# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import json
import os
import unittest
from typing import Any

from tuxemon import prepare

ALL_MONSTERS: int = 196
MAX_TECH_ID: int = 190


def process_json_data(directory: str) -> list[dict[str, Any]]:
    data_list = []
    directory = f"{prepare.fetch('db')}/{directory}/"
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                data_list.append(json.load(f))
    return data_list


class TestTechniqueJSON(unittest.TestCase):
    def setUp(self) -> None:
        sample_data = "technique"
        self.data_list = process_json_data(sample_data)

    def test_nr_jsons(self) -> None:
        self.assertEqual(len(self.data_list), ALL_MONSTERS)

    def test_missing_tech_ids(self) -> None:
        numbers = []
        for data in self.data_list:
            tech_id = data["tech_id"]
            if tech_id > 0:
                numbers.append(tech_id)

        all_numbers = set(range(1, MAX_TECH_ID))
        given_numbers = set(numbers)
        missing = all_numbers - given_numbers
        if missing:
            self.fail(f"There are missing tech_ids: {missing}")

    def test_duplicate_tech_ids(self) -> None:
        numbers = []
        for data in self.data_list:
            tech_id = data["tech_id"]
            if tech_id > 0:
                numbers.append(tech_id)

        duplicates = []
        counts = [0] * (max(numbers) + 1)
        for num in numbers:
            counts[num] += 1
            if counts[num] > 1:
                duplicates.append(num)
        if duplicates:
            self.fail(f"There are duplicates tech_ids: {duplicates}")

    def test_effects_damage_special(self) -> None:
        damage_effect = ("damage", "retaliate", "revenge", "money", "splash")
        techniques = []
        for data in self.data_list:
            slug = data["slug"]
            effects = data["effects"]
            ranges = data["range"]
            if effects and effects[0] in damage_effect and ranges == "special":
                techniques.append(
                    f"{slug}'s 'special' range cannot be used with {damage_effect} effects"
                )
        if techniques:
            print("The following techniques:")
            for monster in techniques:
                print(monster)
            self.fail(f"The 'effect' field cannot contain: {damage_effect}.")

    def test_effects_combinations(self) -> None:
        techniques = {}
        combinations = {
            (
                "damage",
                "healing",
            ): "The 'damage' and 'healing' effect cannot be used together.",
        }
        for data in self.data_list:
            slug = data["slug"]
            effects = data["effects"]
            if effects:
                for combination, error_message in combinations.items():
                    if all(effect in effects for effect in combination):
                        techniques.setdefault(error_message, []).append(
                            f"{slug}'s effects: {effects}."
                        )
        for error_message, technique_list in techniques.items():
            print("The following techniques:")
            for technique in technique_list:
                print(technique)
            self.fail(error_message)
