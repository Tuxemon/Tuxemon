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
from enum import Enum
from operator import itemgetter
from typing import (
    Any,
    Dict,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TypedDict,
    overload,
)

from pydantic import BaseModel, Field, ValidationError, validator

from tuxemon import prepare
from tuxemon.constants import paths

logger = logging.getLogger(__name__)

Target = Mapping[str, int]


class ItemSort(str, Enum):
    food = "food"
    potion = "potion"
    utility = "utility"
    quest = "quest"


class ItemType(str, Enum):
    consumable = "Consumable"
    key_item = "KeyItem"


# TODO: Automatically generate state enum through discovery
states = {
    "MainCombatMenuState": "MainCombatMenuState",
    "WorldState": "WorldState",
    "None": "",
}
State = Enum("State", states)


class ItemModel(BaseModel):
    slug: str = Field(..., description="Slug to use")
    use_item: str = Field(
        ...,
        description="Slug to determine which text is displayed when this item is used",
    )
    use_success: str = Field(
        "generic_success",
        description="Slug to determine which text is displayed when this item is used successfully",
    )
    use_failure: str = Field(
        "generic_failure",
        description="Slug to determine which text is displayed when this item failed to be used",
    )
    sort: ItemSort = Field(..., description="The kind of item this is.")
    sprite: str = Field(..., description="The sprite to use")
    target: Target = Field(
        ..., description="Target mapping of who to use the item on"
    )
    type: ItemType = Field(..., description="The type of item this is")
    usable_in: Sequence[State] = Field(
        ..., description="State(s) where this item can be used."
    )
    conditions: Sequence[str] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[str] = Field(
        [], description="Effects this item will have"
    )

    class Config:
        title = "Item"

    # Validators can be used with custom validation logic.
    # TODO: Ensure this slug exists somewhere in a PO
    @validator("slug")
    def slug_must_exist(cls, v):
        return v


class MonsterMovesetItemModel(BaseModel):
    level_learned: int = Field(
        ..., description="Monster level in which this moveset is learned"
    )
    technique: str = Field(
        ..., description="Name of the technique for this moveset item"
    )


class MonsterEvolutionItemModel(BaseModel):
    path: str = Field(..., description="Path to evolution item")
    at_level: int = Field(
        ...,
        description="The level at which this item can be used for evolution",
    )
    monster_slug: str = Field(
        ..., description="The monster slug that this evolution item applies to"
    )


class MonsterFlairItemModel(BaseModel):
    category: str = Field(..., description="The category of this flair item")
    names: Sequence[str] = Field(..., description="The names")


class MonsterSpritesModel(BaseModel):
    battle1: str = Field(..., description="The battle1 sprite")
    battle2: str = Field(..., description="The battle2 sprite")
    menu1: str = Field(..., description="The menu1 sprite")
    menu2: str = Field(..., description="The menu2 sprite")


class MonsterSoundsModel(BaseModel):
    combat_call: str = Field(
        ..., description="The sound used when entering combat"
    )
    faint_call: str = Field(
        ..., description="The sound used when the monster faints"
    )


class MonsterModel(BaseModel):
    slug: str = Field(..., description="The slug of the monster")
    category: str = Field(..., description="The category of monster")
    ai: str = Field(..., description="The AI to use for this monster")
    weight: float = Field(..., description="The weight of the monster")

    # Optional fields
    sprites: Optional[MonsterSpritesModel]
    shape: str = Field("", description="The shape of the monster")
    types: Sequence[str] = Field([], description="The type(s) of this monster")
    catch_rate: float = Field(0, description="The catch rate of the monster")
    lower_catch_resistance: float = Field(
        0, description="The lower catch resistance of the monster"
    )
    upper_catch_resistance: float = Field(
        0, description="The upper catch resistance of the monster"
    )
    moveset: Sequence[MonsterMovesetItemModel] = Field(
        [], description="The moveset of this monster"
    )
    evolutions: Sequence[MonsterEvolutionItemModel] = Field(
        [], description="The evolutions this monster has"
    )
    flairs: Sequence[MonsterFlairItemModel] = Field(
        [], description="The flairs this monster has"
    )
    sounds: MonsterSoundsModel = Field(
        MonsterSoundsModel(
            combat_call="sound_cry1", faint_call="sound_faint1"
        ),
        description="The sounds this monster has",
    )

    class Config:
        # Validate assignment allows us to assign a default inside a validator
        validate_assignment = True

    # Set the default sprites based on slug. Specifying 'always' is needed
    # because by default pydantic doesn't validate null fields.
    @validator("sprites", always=True)
    def set_default_sprites(cls, v, values, **kwargs):
        slug = values["slug"]
        default = MonsterSpritesModel(
            battle1=f"gfx/sprites/battle/{slug}-front",
            battle2=f"gfx/sprites/battle/{slug}-back",
            menu1=f"gfx/sprites/battle/{slug}-menu01",
            menu2=f"gfx/sprites/battle/{slug}-menu02",
        )
        return v or default


class StatModel(BaseModel):
    value: Optional[int] = Field(None, description="The value of the stat")
    max_deviation: Optional[int] = Field(
        None, description="The maximum deviation of the stat"
    )
    operation: str = Field(
        ..., description="The operation to be done to the stat"
    )
    overridetofull: Optional[bool] = Field(
        None, description="Whether or not to override to full"
    )


class Range(str, Enum):
    special = "special"
    melee = "melee"
    ranged = "ranged"
    touch = "touch"
    reach = "reach"
    reliable = "reliable"


class TechniqueModel(BaseModel):
    slug: str = Field(..., description="The slug of the technique")
    sort: str = Field(..., description="The sort of technique this is")
    category: str = Field(..., description="The category of technique this is")
    icon: str = Field(..., description="The icon to use for the technique")
    effects: Sequence[str] = Field(
        ..., description="Effects this technique uses"
    )
    target: Target = Field(
        ..., description="Target mapping of who this technique is used on"
    )
    animation: Optional[str] = Field(
        None, description="Animation to play for this technique"
    )
    sfx: str = Field(
        ..., description="Sound effect to play when this technique is used"
    )

    # Optional fields
    use_tech: str = Field(
        None,
        description="Slug of what string to display when technique is used",
    )
    use_success: str = Field(
        None,
        description="Slug of what string to display when technique succeeds",
    )
    use_failure: str = Field(
        None, description="Slug of what string to display when technique fails"
    )
    types: Sequence[str] = Field([], description="Type(s) of the technique")
    power: float = Field(0, description="Power of the technique")
    is_fast: bool = Field(
        False, description="Whether or not this is a fast technique"
    )
    is_area: bool = Field(
        False, description="Whether or not this is an area of effect technique"
    )
    recharge: int = Field(0, description="Recharge of this technique")
    range: Range = Field(
        "melee", description="The attack range of this technique"
    )
    accuracy: float = Field(0, description="The accuracy of the technique")
    potency: Optional[float] = Field(
        None, description="How potetent the technique is"
    )
    statspeed: Optional[StatModel] = Field(None)
    stathp: Optional[StatModel] = Field(None)
    statarmour: Optional[StatModel] = Field(None)
    statdodge: Optional[StatModel] = Field(None)
    statmelee: Optional[StatModel] = Field(None)
    statranged: Optional[StatModel] = Field(None)
    userstatspeed: Optional[StatModel] = Field(None)
    userstathp: Optional[StatModel] = Field(None)
    userstatarmour: Optional[StatModel] = Field(None)
    userstatdodge: Optional[StatModel] = Field(None)
    userstatmelee: Optional[StatModel] = Field(None)
    userstatranged: Optional[StatModel] = Field(None)

    # Custom validation for range
    @validator("range")
    def range_validation(cls, v, values, **kwargs):
        # Special indicates that we are not doing damage
        if v == Range.special and "damage" in values["effects"]:
            raise ValueError(
                '"special" range cannot be used with effect "damage"'
            )

        return v


class PartyMemberModel(BaseModel):
    slug: str = Field(..., description="Slug of the monster")
    level: int = Field(..., description="Level of the monster")
    exp_give_mod: float = Field(
        ..., description="Modifier for experience this monster gives"
    )
    exp_req_mod: float = Field(..., description="Experience required modifier")


class NpcModel(BaseModel):
    slug: str = Field(..., description="Slug of the name of the NPC")
    sprite_name: str = Field(
        ..., description="Name of the overworld sprite filename"
    )
    combat_front: str = Field(
        ..., description="Name of the battle front sprite filename"
    )
    combat_back: str = Field(
        ..., description="Name of the battle back sprite filename"
    )
    monsters: Sequence[PartyMemberModel] = Field(
        [], description="List of monsters in the NPCs party"
    )


class BattleGraphicsModel(BaseModel):
    island_back: str = Field(..., description="Sprite used for back combat")
    island_front: str = Field(..., description="Sprite used for front combat")


class EnvironmentModel(BaseModel):
    slug: str = Field(..., description="Slug of the name of the environment")
    battle_music: str = Field(
        ..., description="Filename of the music to use for this environment"
    )
    battle_graphics: BattleGraphicsModel


class EncounterItemModel(BaseModel):
    monster: str = Field(..., description="Monster slug for this encounter")
    encounter_rate: float = Field(..., description="Rate of this encounter")
    level_range: Sequence[int] = Field(
        ..., description="Level range to encounter"
    )


class EncounterModel(BaseModel):
    slug: str = Field(
        ..., description="Slug to uniquely identify this encounter"
    )
    monsters: Sequence[EncounterItemModel] = Field(
        [], description="Monsters encounterable"
    )


class InventoryModel(BaseModel):
    slug: str = Field(
        ..., description="Slug uniquely identifying the inventory"
    )
    inventory: Mapping[str, Optional[int]] = Field(...)


class EconomyItemModel(BaseModel):
    item_name: str = Field(..., description="Name of the item")
    price: int = Field(0, description="Price of the item")
    cost: int = Field(0, description="Cost of the item")


class EconomyModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the economy")
    items: Sequence[EconomyItemModel]


class MusicItemModel(BaseModel):
    slug: str = Field(..., description="Unique slug for the music")
    file: str = Field(..., description="File for the music")


MusicModel: Sequence[MusicItemModel]


def process_targets(json_targets: Target) -> Sequence[str]:
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
            ),
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

    def load(self, directory: str = "all", validate: bool = False) -> None:
        """
        Loads all data from JSON files located under our data path.

        Parameters:
            directory: The directory under mods/tuxemon/db/ to load. Defaults
                to "all".
            validate: Whether or not we should raise an exception if validation
                fails

        """
        self.path = prepare.fetch("db")
        if directory == "all":
            self.load_json("item", validate)
            self.load_json("monster", validate)
            self.load_json("npc", validate)
            self.load_json("technique", validate)
            self.load_json("encounter", validate)
            self.load_json("inventory", validate)
            self.load_json("environment", validate)
            self.load_json("sounds", validate)
            self.load_json("music", validate)
            self.load_json("economy", validate)
        else:
            self.load_json(directory, validate)

    def load_json(self, directory: str, validate: bool = False) -> None:
        """
        Loads all JSON items under a specified path.

        Parameters:
            directory: The directory under mods/tuxemon/db/ to look in.
            validate: Whether or not we should raise an exception if validation
                fails

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
                    self.load_dict(sub, directory, validate)
            else:
                self.load_dict(item, directory, validate)

    def load_dict(
        self, item: Mapping[str, Any], table: str, validate: bool = False
    ) -> None:
        """
        Loads a single json object and adds it to the appropriate db table.

        Parameters:
            item: The json object to load in.
            table: The db table to load the object into.
            validate: Whether or not we should raise an exception if validation
                fails

        """

        if item["slug"] in self.database[table]:
            logger.warning(
                "Error: Item with slug %s was already loaded.", item
            )
            return

        try:
            if table == "economy":
                economy = EconomyModel(**item)
                self.database[table][economy.slug] = economy
            elif table == "encounter":
                encounter = EncounterModel(**item)
                self.database[table][encounter.slug] = encounter
            elif table == "environment":
                env = EnvironmentModel(**item)
                self.database[table][env.slug] = env
            elif table == "inventory":
                inventory = InventoryModel(**item)
                self.database[table][inventory.slug] = inventory
            elif table == "item":
                itm = ItemModel(**item)
                self.database[table][itm.slug] = itm
            elif table == "monster":
                mon = MonsterModel(**item)
                self.database[table][mon.slug] = mon
            # elif table == "music":
            #    mon = (**item)
            #    self.database[table][mon.slug] = mon
            elif table == "npc":
                npc = NpcModel(**item)
                self.database[table][npc.slug] = npc
            # elif table == "sounds":
            #    mon = MonsterSoundsModel(**item)
            #    self.database[table][mon.slug] = mon
            elif table == "technique":
                teq = TechniqueModel(**item)
                self.database[table][teq.slug] = teq
            else:
                self.database[table][item["slug"]] = item
        except ValidationError as e:
            logger.error(f"validation failed for '{item['slug']}': {e}")
            if validate:
                raise e

    @overload
    def lookup(self, slug: str) -> MonsterModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["monster"]) -> MonsterModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["technique"]) -> TechniqueModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["item"]) -> ItemModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["npc"]) -> NpcModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["encounter"]) -> EncounterModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["inventory"]) -> InventoryModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["economy"]) -> EconomyModel:
        pass

    @overload
    def lookup(
        self,
        slug: str,
        table: Literal["environment"],
    ) -> EnvironmentModel:
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
        return self.database[table][slug]

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
            logger.debug(
                f"Could not find a file record for slug {slug}, did you remember to create a database record?"
            )

        return filename


# Global database container
db = JSONDatabase()
