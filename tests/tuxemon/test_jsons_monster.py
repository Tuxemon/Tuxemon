# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import json
import os
import unittest
from typing import Any

from tuxemon import prepare


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
        self.assertEqual(len(self.data_list), 298)

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
