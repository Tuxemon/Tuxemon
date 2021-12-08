#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# db Database handling module.
#
#

from __future__ import annotations
import json
import logging
import os
from operator import itemgetter

from tuxemon import prepare
from typing import Any, Mapping, Dict, Sequence, TypedDict, overload, Literal,\
    Optional

logger = logging.getLogger(__name__)


JSONTarget = Mapping[str, int]


class JSONItemOptionalFields(TypedDict, total=False):
    conditions: Sequence[str]
    effects: Sequence[str]


class JSONItem(JSONItemOptionalFields):
    slug: str
    use_item: str
    use_success: str
    use_failure: str
    sort: str
    sprite: str
    target: JSONTarget
    type: str
    usable_in: Sequence[str]


class JSONMonsterMovesetItem(TypedDict):
    level_learned: int
    technique: str


class JSONMonsterEvolutionItem(TypedDict):
    path: str
    at_level: int
    monster_slug: str


class JSONMonsterFlairItem(TypedDict):
    category: str
    names: Sequence[str]


class JSONMonsterSprites(TypedDict):
    battle1: str
    battle2: str
    menu1: str
    menu2: str


class JSONMonsterSounds(TypedDict, total=False):
    combat_call: str
    faint_call: str


class JSONMonsterOptionalFields(TypedDict, total=False):
    shape: str
    types: Sequence[str]
    catch_rate: float
    lower_catch_resistance: float
    upper_catch_resistance: float
    moveset: Sequence[JSONMonsterMovesetItem]
    evolutions: Sequence[JSONMonsterEvolutionItem]
    flairs: Sequence[JSONMonsterFlairItem]
    sounds: JSONMonsterSounds


class JSONMonster(JSONMonsterOptionalFields):
    slug: str
    category: str
    ai: str
    weight: float
    sprites: JSONMonsterSprites


class JSONStat(TypedDict, total=False):
    value: int
    max_deviation: int
    operation: str
    overridetofull: bool


class JSONTechniqueOptionalFields(TypedDict, total=False):
    use_tech: str
    use_success: str
    use_failure: str
    types: Sequence[str]
    power: float
    is_fast: bool
    recharge: int
    is_area: bool
    range: str
    accuracy: float
    potency: float
    statspeed: JSONStat
    stathp: JSONStat
    statarmour: JSONStat
    statdodge: JSONStat
    statmelee: JSONStat
    statranged: JSONStat
    userstatspeed: JSONStat
    usertathp: JSONStat
    userstatarmour: JSONStat
    userstatdodge: JSONStat
    userstatmelee: JSONStat
    userstatranged: JSONStat


class JSONTechnique(JSONTechniqueOptionalFields):
    slug: str
    sort: str
    category: str
    icon: str
    effects: Sequence[str]
    target: JSONTarget
    animation: str
    sfx: str


class JSONNpc(TypedDict):
    slug: str
    sprite_name: str
    combat_front: str
    combat_back: str


class JSONBattleGraphics(TypedDict):
    island_back: str
    island_front: str


class JSONEnvironment(TypedDict):
    slug: str
    battle_music: str
    battle_graphics: JSONBattleGraphics


class JSONEncounterItem(TypedDict):
    monster: str
    encounter_rate: float
    level_range: Sequence[int]


class JSONEncounter(TypedDict):
    slug: str
    monsters: Sequence[JSONEncounterItem]


class JSONInventory(TypedDict):
    slug: str
    inventory: Mapping[str, Optional[int]]

class JSONEconomyItem(TypedDict):
    item: str
    price: int
    cost: int

class JSONEconomy(TypedDict):
    slug: str
    parent: Optional[str]
    items: Sequence[JSONEconomyItem]

def process_targets(json_targets: JSONTarget) -> Sequence[str]:
    """Return values in order of preference for targeting things.

    example: ["own monster", "enemy monster"]

    Parameters:
        json_targets: Dictionary of targets.

    Returns:
        Order of preference for targets.

    """
    return list(
        map(
            itemgetter(0),
            filter(
                itemgetter(1),
                sorted(
                    json_targets.items(),
                    key=itemgetter(1),
                    reverse=True,
                ),
            )
        )
    )


class JSONDatabase:
    """
    Handles connecting to the game database for resources.

    Examples of such resources include monsters, stats, etc.

    """

    def __init__(self, dir: str = "all") -> None:
        self.path = ""
        self.database: Dict[str, Dict[str, Any]] = {
            "item": {},
            "monster": {},
            "npc": {},
            "technique": {},
            "encounter": {},
            "inventory": {},
            "environment": {},
            "sounds": {},
            "music": {},
            "economy": {},
        }
        # self.load(dir)

    def load(self, directory: str = "all") -> None:
        """
        Loads all data from JSON files located under our data path.

        Parameters:
            directory: The directory under mods/tuxemon/db/ to load. Defaults
                to "all".

        """
        self.path = prepare.fetch("db")
        if directory == "all":
            self.load_json("item")
            self.load_json("monster")
            self.load_json("npc")
            self.load_json("technique")
            self.load_json("encounter")
            self.load_json("inventory")
            self.load_json("environment")
            self.load_json("sounds")
            self.load_json("music")
            self.load_json("economy")
        else:
            self.load_json(directory)

    def load_json(self, directory: str) -> None:
        """
        Loads all JSON items under a specified path.

        Parameters:
            directory: The directory under mods/tuxemon/db/ to look in.

        """
        for json_item in os.listdir(os.path.join(self.path, directory)):

            # Only load .json files.
            if not json_item.endswith(".json"):
                continue

            # Load our json as a dictionary.
            with open(os.path.join(self.path, directory, json_item)) as fp:
                try:
                    item = json.load(fp)
                except ValueError:
                    logger.error("invalid JSON " + json_item)
                    raise

            if type(item) is list:
                for sub in item:
                    self.load_dict(sub, directory)
            else:
                self.load_dict(item, directory)

    def load_dict(self, item: Mapping[str, Any], table: str) -> None:
        """
        Loads a single json object and adds it to the appropriate db table.

        Parameters:
            item: The json object to load in.
            table: The db table to load the object into.

        """

        if item["slug"] not in self.database[table]:
            self.database[table][item["slug"]] = item
        else:
            logger.warning("Error: Item with slug %s was already loaded.", item)

    @overload
    def lookup(self, slug: str) -> JSONMonster:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["monster"]) -> JSONMonster:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["technique"]) -> JSONTechnique:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["item"]) -> JSONItem:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["npc"]) -> JSONNpc:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["encounter"]) -> JSONEncounter:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["inventory"]) -> JSONInventory:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["economy"]) -> JSONEconomy:
        pass

    @overload
    def lookup(
        self,
        slug: str,
        table: Literal["environment"],
    ) -> JSONEnvironment:
        pass

    def lookup(self, slug: str, table: str = "monster") -> Mapping[str, Any]:
        """
        Looks up a monster, technique, item, or npc based on slug.

        Parameters:
            slug: The slug of the monster, technique, item, or npc.  A short
                English identifier.
            table: Which index to do the search in. Can be: "monster",
                "item", "npc", or "technique".

        Returns:
            A dictionary from the resulting lookup.

        """
        return set_defaults(self.database[table][slug], table)

    def lookup_file(self, table: str, slug: str) -> str:
        """
        Does a lookup with the given slug in the given table.

        It expects a dictionary with two keys, 'slug' and 'file'.

        Parameters:
            slug: The slug of the file record.
            table: The table to do the lookup in, such as "sounds" or "music".

        Returns:
            The 'file' property of the resulting dictionary OR the slug if it
            doesn't exist.

        """

        filename = self.database[table][slug]["file"] or slug
        if filename == slug:
            logger.debug(f"Could not find a file record for slug {slug}, did you remember to create a database record?")

        return filename


def set_defaults(results: Dict[str, Any], table: str) -> Mapping[str, Any]:
    if table == "monster":
        name = results["slug"]

        sprites = results.setdefault("sprites", {})

        for key, view in (
            ("battle1", "front"),
            ("battle2", "back"),
            ("menu1", "menu01"),
            ("menu2", "menu02"),
        ):
            if not results.get(key):
                sprites[key] = f"gfx/sprites/battle/{name}-{view}"

    return results


# Global database container
db = JSONDatabase()
