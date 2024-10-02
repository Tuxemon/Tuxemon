# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import difflib
import json
import logging
import os
import sys
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union, overload

from PIL import Image
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)

from tuxemon import prepare
from tuxemon.constants import paths
from tuxemon.locale import T

logger = logging.getLogger(__name__)

# Load the default translator for data validation
T.collect_languages(False)
T.load_translator()

SurfaceKeys = prepare.SURFACE_KEYS


class Direction(str, Enum):
    up = "up"
    down = "down"
    left = "left"
    right = "right"


class Orientation(str, Enum):
    horizontal = "horizontal"
    vertical = "vertical"


# ItemSort defines the sort of item an item is.
class ItemSort(str, Enum):
    food = "food"
    potion = "potion"
    utility = "utility"
    quest = "quest"


class PlagueType(str, Enum):
    healthy = "healthy"
    inoculated = "inoculated"
    infected = "infected"


class GenderType(str, Enum):
    neuter = "neuter"
    male = "male"
    female = "female"


class SkinSprite(str, Enum):
    light = "light"
    tanned = "tanned"
    dark = "dark"
    albino = "albino"
    orc = "orc"


class TasteWarm(str, Enum):
    tasteless = "tasteless"
    peppy = "peppy"
    salty = "salty"
    hearty = "hearty"
    zesty = "zesty"
    refined = "refined"


class TasteCold(str, Enum):
    tasteless = "tasteless"
    mild = "mild"
    sweet = "sweet"
    soft = "soft"
    flakey = "flakey"
    dry = "dry"


class ElementType(str, Enum):
    aether = "aether"
    wood = "wood"
    fire = "fire"
    earth = "earth"
    metal = "metal"
    water = "water"


class ItemCategory(str, Enum):
    none = "none"
    badge = "badge"
    elements = "elements"
    fossil = "fossil"
    morph = "morph"
    revive = "revive"
    potion = "potion"
    technique = "technique"
    phone = "phone"
    fish = "fish"
    destroy = "destroy"
    capture = "capture"
    stats = "stats"


class OutputBattle(str, Enum):
    won = "won"
    lost = "lost"
    draw = "draw"


class MonsterShape(str, Enum):
    default = "default"
    blob = "blob"
    brute = "brute"
    dragon = "dragon"
    flier = "flier"
    grub = "grub"
    humanoid = "humanoid"
    hunter = "hunter"
    landrace = "landrace"
    leviathan = "leviathan"
    piscine = "piscine"
    polliwog = "polliwog"
    serpent = "serpent"
    sprite = "sprite"
    varmint = "varmint"


class SeenStatus(str, Enum):
    unseen = "unseen"
    seen = "seen"
    caught = "caught"


class MapType(str, Enum):
    notype = "notype"
    town = "town"
    route = "route"
    clinic = "clinic"
    shop = "shop"
    dungeon = "dungeon"


class StatType(str, Enum):
    armour = "armour"
    dodge = "dodge"
    hp = "hp"
    melee = "melee"
    ranged = "ranged"
    speed = "speed"


class EvolutionStage(str, Enum):
    standalone = "standalone"
    basic = "basic"
    stage1 = "stage1"
    stage2 = "stage2"


class MissionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class EntityFacing(str, Enum):
    front = "front"
    back = "back"
    left = "left"
    right = "right"


class MusicStatus(str, Enum):
    playing = "playing"
    paused = "paused"
    stopped = "stopped"


class Comparison(str, Enum):
    less_than = "less_than"
    less_or_equal = "less_or_equal"
    greater_than = "greater_than"
    greater_or_equal = "greater_or_equal"
    equals = "equals"
    not_equals = "not_equals"


# TODO: Automatically generate state enum through discovery
State = Enum(
    "State",
    {
        "MainCombatMenuState": "MainCombatMenuState",
        "MainParkMenuState": "MainParkMenuState",
        "WorldState": "WorldState",
        "None": "",
    },
)


class ItemBehaviors(BaseModel):
    consumable: bool = Field(
        True, description="Whether or not this item is consumable."
    )
    visible: bool = Field(
        True, description="Whether or not this item is visible."
    )
    requires_monster_menu: bool = Field(
        True, description="Whether the monster menu is required to be open."
    )
    show_dialog_on_failure: bool = Field(
        True, description="Whether to show a dialogue after a failed use."
    )
    show_dialog_on_success: bool = Field(
        True, description="Whether to show a dialogue after a successful use."
    )
    throwable: bool = Field(
        False, description="Whether or not this item is throwable."
    )


class ItemModel(BaseModel):
    model_config = ConfigDict(title="Item")
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
    category: ItemCategory = Field(
        ..., description="The category of item this is"
    )
    usable_in: Sequence[State] = Field(
        ..., description="State(s) where this item can be used."
    )
    behaviors: ItemBehaviors
    # TODO: We'll need some more advanced validation logic here to parse item
    # conditions and effects to ensure they are formatted properly.
    conditions: Sequence[str] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[str] = Field(
        [], description="Effects this item will have"
    )
    flip_axes: Literal["", "x", "y", "xy"] = Field(
        "",
        description="Axes along which technique animation should be flipped",
    )
    animation: Optional[str] = Field(
        None, description="Animation to play for this technique"
    )
    world_menu: tuple[int, str, str] = Field(
        None,
        description="Item adds to World Menu a button (position, label -inside the PO -,state, eg. 3:nu_phone:PhoneState)",
    )

    # Validate fields that refer to translated text
    @field_validator("use_item", "use_success", "use_failure")
    def translation_exists(cls: ItemModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_item(cls: ItemModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    # Validate resources that should exist
    @field_validator("sprite")
    def file_exists(cls: ItemModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.ITEM_SIZE):
            return v
        raise ValueError(f"the sprite {v} doesn't exist in the db")

    @field_validator("animation")
    def animation_exists(cls: ItemModel, v: Optional[str]) -> Optional[str]:
        file: str = f"animations/item/{v}_00.png"
        if (
            not v
            or has.db_entry("animation", v)
            and has.size(file, prepare.NATIVE_RESOLUTION)
        ):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")

    @field_validator("conditions")
    def check_conditions(cls: ItemModel, v: Sequence[str]) -> Sequence[str]:
        if not v or has.check_conditions(v):
            return v
        raise ValueError(f"the conditions {v} aren't correctly formatted")


class ShapeModel(BaseModel):
    slug: MonsterShape = Field(..., description="Slug of the shape")
    armour: int = Field(..., description="Armour value")
    dodge: int = Field(..., description="Dodge value")
    hp: int = Field(..., description="HP value")
    melee: int = Field(..., description="Melee value")
    ranged: int = Field(..., description="Ranged value")
    speed: int = Field(..., description="Speed value")

    @field_validator("slug")
    def translation_exists_shape(cls: ShapeModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class MonsterMovesetItemModel(BaseModel):
    level_learned: int = Field(
        ..., description="Monster level in which this moveset is learned", gt=0
    )
    technique: str = Field(
        ...,
        description="Name of the technique for this moveset item",
        json_schema_extra={"unique": True},
    )

    @field_validator("technique")
    def technique_exists(cls: MonsterMovesetItemModel, v: str) -> str:
        if has.db_entry("technique", v):
            return v
        raise ValueError(f"the technique {v} doesn't exist in the db")


class MonsterHistoryItemModel(BaseModel):
    mon_slug: str = Field(..., description="The monster in the evolution path")
    evo_stage: EvolutionStage = Field(
        ..., description="The evolution stage of the monster"
    )

    @field_validator("mon_slug")
    def monster_exists(cls: MonsterHistoryItemModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class MonsterEvolutionItemModel(BaseModel):
    monster_slug: str = Field(
        ..., description="The monster slug that this evolution item applies to"
    )
    # optional fields
    at_level: Optional[int] = Field(
        None,
        description="The level at which the monster evolves.",
        ge=0,
    )
    element: Optional[ElementType] = Field(
        None,
        description="The element type that the monster must match to evolve.",
    )
    gender: Optional[GenderType] = Field(
        None,
        description="The required gender of the monster for evolution.",
    )
    item: Optional[str] = Field(
        None,
        description="The item that the monster must have to evolve.",
    )
    inside: bool = Field(
        None,
        description="Whether the monster must be inside to evolve.",
    )
    traded: bool = Field(
        None,
        description="Whether the monster must have been traded to evolve.",
    )
    variables: Optional[Sequence[str]] = Field(
        None,
        description="The game variables that must exist and match a specific value for the monster to evolve.",
        min_length=1,
    )
    stats: Optional[str] = Field(
        None,
        description="The statistic comparison required for the monster to evolve (e.g., greater_than, less_than, etc.).",
    )
    steps: Optional[int] = Field(
        None,
        description="The minimum number of steps the monster must have walked to evolve.",
    )
    tech: Optional[str] = Field(
        None,
        description="The technique that a monster in the party must have for the evolution to occur.",
    )
    moves: Optional[Sequence[str]] = Field(
        None,
        description="The techniques that the monster must have learned for the evolution to occur.",
        min_length=1,
        max_length=prepare.MAX_MOVES,
    )
    bond: Optional[str] = Field(
        None,
        description="The bond value comparison required for the monster to evolve (e.g., greater_than, less_than, etc.).",
    )
    party: Optional[Sequence[str]] = Field(
        None,
        description="The slug of the monsters that must be in the party for the evolution to occur.",
        min_length=1,
        max_length=prepare.PARTY_LIMIT - 1,
    )
    taste_cold: Optional[TasteCold] = Field(
        None,
        description="The required taste cold value for the monster to evolve.",
    )
    taste_warm: Optional[TasteWarm] = Field(
        None,
        description="The required taste warm value for the monster to evolve.",
    )

    @field_validator("moves")
    def move_exists(
        cls: MonsterEvolutionItemModel, v: Optional[Sequence[str]]
    ) -> Optional[Sequence[str]]:
        if v:
            for element in v:
                if not has.db_entry("technique", element):
                    raise ValueError(
                        f"A technique {element} doesn't exist in the db"
                    )
        return v

    @field_validator("tech")
    def technique_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.db_entry("technique", v):
            return v
        raise ValueError(f"the technique {v} doesn't exist in the db")

    @field_validator("monster_slug")
    def monster_exists(cls: MonsterEvolutionItemModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")

    @field_validator("party")
    def party_exists(
        cls: MonsterEvolutionItemModel, v: Sequence[str]
    ) -> Sequence[str]:
        if v:
            for element in v:
                if not has.db_entry("monster", element):
                    raise ValueError(
                        f"A monster {element} doesn't exist in the db"
                    )
        return v

    @field_validator("item")
    def item_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")

    @field_validator("variables")
    def variables_exists(
        cls: MonsterEvolutionItemModel, v: Optional[Sequence[str]]
    ) -> Optional[Sequence[str]]:
        if v is None:
            return v
        if len(v) != len(set(v)):
            raise ValueError("The sequence contains duplicate variables")
        for variable in v:
            if (
                not variable
                or len(variable.split(":")) != 2
                or variable[0] == ":"
                or variable[-1] == ":"
            ):
                raise ValueError(
                    f"the variable {variable} isn't formatted correctly"
                )
        return v

    @field_validator("stats")
    def stats_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        stats = list(StatType)
        comparison = list(Comparison)
        param = v.split(":") if v else []
        if not v or len(param) == 3:
            if param[1] not in comparison:
                raise ValueError(
                    f"the comparison {param[1]} doesn't exist among {comparison}"
                )
            if param[0] not in stats:
                raise ValueError(
                    f"the stat {param[0]} doesn't exist among {stats}"
                )
            if param[2] not in stats:
                raise ValueError(
                    f"the stat {param[2]} doesn't exist among {stats}"
                )
            return v
        raise ValueError(f"the stats {v} isn't formatted correctly")

    @field_validator("bond")
    def bond_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        comparison = list(Comparison)
        param = v.split(":") if v else []
        if not v or len(param) == 2:
            if param[0] not in comparison:
                raise ValueError(
                    f"the comparison {param[0]} doesn't exist among {comparison}"
                )
            if not param[1].isdigit():
                raise ValueError(f"{param[1]} isn't a number (int)")
            lower, upper = prepare.BOND_RANGE
            if int(param[1]) < lower or int(param[1]) > upper:
                raise ValueError(
                    f"the bond is between {lower} and {upper} ({v})"
                )
            return v
        raise ValueError(f"the stats {v} isn't formatted correctly")


class MonsterFlairItemModel(BaseModel):
    category: str = Field(..., description="The category of this flair item")
    names: Sequence[str] = Field(..., description="The names")


class MonsterSpritesModel(BaseModel):
    battle1: str = Field(..., description="The battle1 sprite")
    battle2: str = Field(..., description="The battle2 sprite")
    menu1: str = Field(..., description="The menu1 sprite")
    menu2: str = Field(..., description="The menu2 sprite")

    # Validate resources that should exist
    @field_validator("battle1", "battle2")
    def battle_exists(cls: MonsterSpritesModel, v: str) -> str:
        if has.file(f"{v}.png") and has.size(f"{v}.png", prepare.MONSTER_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {v}")

    @field_validator("menu1", "menu2")
    def menu_exists(cls: MonsterSpritesModel, v: str) -> str:
        if has.file(f"{v}.png") and has.size(
            f"{v}.png", prepare.MONSTER_SIZE_MENU
        ):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class MonsterSoundsModel(BaseModel):
    combat_call: str = Field(
        ..., description="The sound used when entering combat"
    )
    faint_call: str = Field(
        ..., description="The sound used when the monster faints"
    )

    @field_validator("combat_call")
    def combat_call_exists(cls: MonsterSoundsModel, v: str) -> str:
        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")

    @field_validator("faint_call")
    def faint_call_exists(cls: MonsterSoundsModel, v: str) -> str:
        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


# Validate assignment allows us to assign a default inside a validator
class MonsterModel(BaseModel, validate_assignment=True):
    slug: str = Field(..., description="The slug of the monster")
    category: str = Field(..., description="The category of monster")
    txmn_id: int = Field(..., description="The id of the monster")
    height: float = Field(..., description="The height of the monster", gt=0.0)
    weight: float = Field(..., description="The weight of the monster", gt=0.0)
    stage: EvolutionStage = Field(
        ..., description="The evolution stage of the monster"
    )
    randomly: bool = Field(
        True,
        description="Whether or not this monster will be picked by random",
    )

    # Optional fields
    sprites: Annotated[
        Optional[MonsterSpritesModel], Field(validate_default=True)
    ] = None
    shape: MonsterShape = Field(..., description="The shape of the monster")
    tags: Sequence[str] = Field(
        ..., description="The tags of the monster", min_length=1
    )
    types: Sequence[ElementType] = Field(
        [], description="The type(s) of this monster"
    )
    catch_rate: float = Field(
        ...,
        description="The catch rate of the monster",
        ge=prepare.CATCH_RATE_RANGE[0],
        le=prepare.CATCH_RATE_RANGE[1],
    )
    possible_genders: Sequence[GenderType] = Field(
        [], description="Valid genders for the monster"
    )
    lower_catch_resistance: float = Field(
        ...,
        description="The lower catch resistance of the monster",
        ge=prepare.CATCH_RESISTANCE_RANGE[0],
        le=prepare.CATCH_RESISTANCE_RANGE[1],
    )
    upper_catch_resistance: float = Field(
        ...,
        description="The upper catch resistance of the monster",
        ge=prepare.CATCH_RESISTANCE_RANGE[0],
        le=prepare.CATCH_RESISTANCE_RANGE[1],
    )
    moveset: Sequence[MonsterMovesetItemModel] = Field(
        [], description="The moveset of this monster", min_length=1
    )
    history: Sequence[MonsterHistoryItemModel] = Field(
        [], description="The evolution history of this monster"
    )
    evolutions: Sequence[MonsterEvolutionItemModel] = Field(
        [], description="The evolutions this monster has"
    )
    flairs: Sequence[MonsterFlairItemModel] = Field(
        [], description="The flairs this monster has"
    )
    sounds: Optional[MonsterSoundsModel] = Field(
        None,
        description="The sounds this monster has",
    )

    # Set the default sprites based on slug. Specifying 'always' is needed
    # because by default pydantic doesn't validate null fields.
    @field_validator("sprites")
    def set_default_sprites(
        cls: MonsterModel, v: str, info: ValidationInfo
    ) -> Union[str, MonsterSpritesModel]:
        slug = info.data.get("slug")
        default = MonsterSpritesModel(
            battle1=f"gfx/sprites/battle/{slug}-front",
            battle2=f"gfx/sprites/battle/{slug}-back",
            menu1=f"gfx/sprites/battle/{slug}-menu01",
            menu2=f"gfx/sprites/battle/{slug}-menu02",
        )
        return v or default

    @field_validator("category")
    def translation_exists_category(cls: MonsterModel, v: str) -> str:
        if has.translation(f"cat_{v}"):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class StatModel(BaseModel):
    value: float = Field(
        0.0, description="The value of the stat", ge=0.0, le=2.0
    )
    max_deviation: int = Field(
        0, description="The maximum deviation of the stat"
    )
    operation: str = Field(
        "+", description="The operation to be done to the stat"
    )
    overridetofull: bool = Field(
        False, description="Whether or not to override to full"
    )


class Range(str, Enum):
    special = "special"
    melee = "melee"
    ranged = "ranged"
    touch = "touch"
    reach = "reach"
    reliable = "reliable"


class TechCategory(str, Enum):
    animal = "animal"
    simple = "simple"
    basic = "basic"
    exotic = "exotic"
    reserved = "reserved"
    powerful = "powerful"
    condition_imposer = "condition_imposer"
    notype = "notype"


# TechSort defines the sort of technique a technique is.
class TechSort(str, Enum):
    damage = "damage"
    meta = "meta"


class CategoryCondition(str, Enum):
    negative = "negative"
    positive = "positive"
    neutral = "neutral"


class ResponseCondition(str, Enum):
    replaced = "replaced"
    removed = "removed"


class TargetModel(BaseModel):
    enemy_monster: bool = Field(
        ..., description="Whether the enemy monster is the target."
    )
    enemy_team: bool = Field(
        ..., description="Whether the enemy team is the target."
    )
    enemy_trainer: bool = Field(
        ..., description="Whether the enemy trainer is the target."
    )
    own_monster: bool = Field(
        ..., description="Whether the own monster is the target."
    )
    own_team: bool = Field(
        ..., description="Whether the own team is the target."
    )
    own_trainer: bool = Field(
        ..., description="Whether the own trainer is the target."
    )

    @field_validator(
        "enemy_monster",
        "enemy_team",
        "enemy_trainer",
        "own_monster",
        "own_team",
        "own_trainer",
    )
    def validate_bool_field(cls: TargetModel, v: bool) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f"One of the targets {v} isn't a boolean")
        return v


class TechniqueModel(BaseModel):
    slug: str = Field(..., description="The slug of the technique")
    sort: TechSort = Field(..., description="The sort of technique this is")
    icon: str = Field(None, description="The icon to use for the technique")
    category: TechCategory = Field(
        ...,
        description="The tags of the technique",
    )
    tags: Sequence[str] = Field(
        ..., description="The tags of the technique", min_length=1
    )
    conditions: Sequence[str] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[str] = Field(
        [], description="Effects this technique uses"
    )
    flip_axes: Literal["", "x", "y", "xy"] = Field(
        ...,
        description="Axes along which technique animation should be flipped",
    )
    target: TargetModel
    animation: Optional[str] = Field(
        None, description="Animation to play for this technique"
    )
    sfx: str = Field(
        ..., description="Sound effect to play when this technique is used"
    )

    # Optional fields
    use_tech: Optional[str] = Field(
        None,
        description="Slug of what string to display when technique is used",
    )
    use_success: Optional[str] = Field(
        None,
        description="Slug of what string to display when technique succeeds",
    )
    use_failure: Optional[str] = Field(
        None,
        description="Slug of what string to display when technique fails",
    )
    types: Sequence[ElementType] = Field(
        [], description="Type(s) of the technique"
    )
    usable_on: bool = Field(
        False,
        description="Whether or not the technique can be used outside of combat",
    )
    power: float = Field(
        ...,
        description="Power of the technique",
        ge=prepare.POWER_RANGE[0],
        le=prepare.POWER_RANGE[1],
    )
    is_fast: bool = Field(
        False, description="Whether or not this is a fast technique"
    )
    randomly: bool = Field(
        True,
        description="Whether or not this technique will be picked by random",
    )
    healing_power: float = Field(
        0.0,
        description="Value of healing power.",
        ge=prepare.HEALING_POWER_RANGE[0],
        le=prepare.HEALING_POWER_RANGE[1],
    )
    recharge: int = Field(
        0,
        description="Recharge of this technique",
        ge=prepare.RECHARGE_RANGE[0],
        le=prepare.RECHARGE_RANGE[1],
    )
    range: Range = Field(..., description="The attack range of this technique")
    tech_id: int = Field(..., description="The id of this technique")
    accuracy: float = Field(
        ...,
        description="The accuracy of the technique",
        ge=prepare.ACCURACY_RANGE[0],
        le=prepare.ACCURACY_RANGE[1],
    )
    potency: float = Field(
        ...,
        description="How potent the technique is",
        ge=prepare.POTENCY_RANGE[0],
        le=prepare.POTENCY_RANGE[1],
    )

    # Validate resources that should exist
    @field_validator("icon")
    def file_exists(cls: TechniqueModel, v: str) -> str:
        if v and has.file(v) and has.size(v, prepare.TECH_ICON_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")

    # Validate fields that refer to translated text
    @field_validator("use_tech", "use_success", "use_failure")
    def translation_exists(
        cls: TechniqueModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_tech(cls: TechniqueModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    # Custom validation for range
    @field_validator("range")
    def range_validation(
        cls: TechniqueModel, v: Range, info: ValidationInfo
    ) -> Range:
        # Special indicates that we are not doing damage
        if v == Range.special and any(
            effect in info.data["effects"]
            for effect in [
                "damage",
                "area",
                "retaliate",
                "revenge",
                "money",
                "splash",
            ]
        ):
            raise ValueError(
                '"special" range cannot be used with effects "damage", "area", "retaliate", "revenge", "money", or "splash"'
            )
        return v

    @field_validator("animation")
    def animation_exists(
        cls: TechniqueModel, v: Optional[str]
    ) -> Optional[str]:
        file: str = f"animations/technique/{v}_00.png"
        if (
            not v
            or has.db_entry("animation", v)
            and has.size(file, prepare.NATIVE_RESOLUTION)
        ):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")

    @field_validator("conditions")
    def check_conditions(
        cls: TechniqueModel, v: Sequence[str]
    ) -> Sequence[str]:
        if not v or has.check_conditions(v):
            return v
        raise ValueError(f"the conditions {v} aren't correctly formatted")

    @field_validator("sfx")
    def sfx_tech_exists(cls: TechniqueModel, v: str) -> str:
        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class ConditionModel(BaseModel):
    slug: str = Field(..., description="The slug of the condition")
    sort: TechSort = Field(..., description="The sort of condition this is")
    icon: str = Field(None, description="The icon to use for the condition")
    conditions: Sequence[str] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[str] = Field(
        [], description="Effects this condition uses"
    )
    flip_axes: Literal["", "x", "y", "xy"] = Field(
        ...,
        description="Axes along which condition animation should be flipped",
    )
    target: TargetModel
    animation: Optional[str] = Field(
        None, description="Animation to play for this condition"
    )
    sfx: str = Field(
        ..., description="Sound effect to play when this condition is used"
    )
    bond: bool = Field(
        False,
        description="Whether or not there is a bond between attacker and defender",
    )
    duration: int = Field(
        0, description="How many turns the condition is supposed to last"
    )

    # Optional fields
    category: Optional[CategoryCondition] = Field(
        None, description="Category status: positive or negative"
    )
    repl_pos: Optional[ResponseCondition] = Field(
        None, description="How to reply to a positive status"
    )
    repl_neg: Optional[ResponseCondition] = Field(
        None, description="How to reply to a negative status"
    )
    repl_tech: Optional[str] = Field(
        None,
        description="With which status or technique reply after a tech used",
    )
    repl_item: Optional[str] = Field(
        None,
        description="With which status or technique reply after an item used",
    )
    gain_cond: Optional[str] = Field(
        None,
        description="Slug of what string to display when condition is gained",
    )
    use_success: Optional[str] = Field(
        None,
        description="Slug of what string to display when condition succeeds",
    )
    use_failure: Optional[str] = Field(
        None,
        description="Slug of what string to display when condition fails",
    )
    range: Range = Field(..., description="The attack range of this condition")
    cond_id: int = Field(..., description="The id of this condition")
    statspeed: Optional[StatModel] = Field(None)
    stathp: Optional[StatModel] = Field(None)
    statarmour: Optional[StatModel] = Field(None)
    statdodge: Optional[StatModel] = Field(None)
    statmelee: Optional[StatModel] = Field(None)
    statranged: Optional[StatModel] = Field(None)

    # Validate resources that should exist
    @field_validator("icon")
    def file_exists(cls: ConditionModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.STATUS_ICON_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")

    # Validate fields that refer to translated text
    @field_validator("gain_cond", "use_success", "use_failure")
    def translation_exists(
        cls: ConditionModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_cond(cls: ConditionModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("animation")
    def animation_exists(
        cls: ConditionModel, v: Optional[str]
    ) -> Optional[str]:
        file: str = f"animations/technique/{v}_00.png"
        if (
            not v
            or has.db_entry("animation", v)
            and has.size(file, prepare.NATIVE_RESOLUTION)
        ):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")

    @field_validator("repl_tech", "repl_item")
    def status_exists(cls: ConditionModel, v: Optional[str]) -> Optional[str]:
        if (
            not v
            or has.db_entry("condition", v)
            or has.db_entry("technique", v)
        ):
            return v
        raise ValueError(f"the status {v} doesn't exist in the db")

    @field_validator("conditions")
    def check_conditions(
        cls: ConditionModel, v: Sequence[str]
    ) -> Sequence[str]:
        if not v or has.check_conditions(v):
            return v
        raise ValueError(f"the conditions {v} aren't correctly formatted")

    @field_validator("sfx")
    def sfx_cond_exists(cls: ConditionModel, v: str) -> str:
        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class PartyMemberModel(BaseModel):
    slug: str = Field(..., description="Slug of the monster")
    level: int = Field(..., description="Level of the monster", gt=0)
    money_mod: int = Field(
        ..., description="Modifier for money this monster gives", gt=0
    )
    exp_req_mod: int = Field(
        ..., description="Experience required modifier", gt=0
    )
    gender: GenderType = Field(..., description="Gender of the monster")

    @field_validator("slug")
    def monster_exists(cls: PartyMemberModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class BagItemModel(BaseModel):
    slug: str = Field(..., description="Slug of the item")
    quantity: int = Field(..., description="Quantity of the item")

    @field_validator("slug")
    def item_exists(cls: BagItemModel, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")


class NpcTemplateModel(BaseModel):
    sprite_name: str = Field(
        ..., description="Name of the overworld sprite filename"
    )
    combat_front: str = Field(
        ..., description="Name of the battle front sprite filename"
    )
    slug: str = Field(
        ..., description="Name of the battle back sprite filename"
    )

    @field_validator("combat_front")
    def combat_file_exists(cls: NpcTemplateModel, v: str) -> str:
        file: str = f"gfx/sprites/player/{v}.png"
        if has.file(file):
            return v
        raise ValueError(f"{file} doesn't exist in the db")

    @field_validator("sprite_name")
    def sprite_exists(cls: NpcTemplateModel, v: str) -> str:
        sprite = f"sprites/{v}_front.png"
        sprite = f"sprites/{v}_back.png"
        sprite = f"sprites/{v}_right.png"
        sprite = f"sprites/{v}_left.png"
        sprite_obj: str = f"sprites_obj/{v}.png"
        if (
            has.file(sprite)
            and has.size(sprite, prepare.SPRITE_SIZE)
            or has.file(sprite_obj)
            and has.size(sprite_obj, prepare.NATIVE_RESOLUTION)
        ):
            return v
        raise ValueError(f"the sprite {v} doesn't exist in the db")

    @field_validator("slug")
    def template_exists(cls: NpcTemplateModel, v: str) -> str:
        if has.db_entry("template", v):
            return v
        raise ValueError(f"the template {v} doesn't exist in the db")


class NpcModel(BaseModel):
    slug: str = Field(..., description="Slug of the name of the NPC")
    forfeit: bool = Field(False, description="Whether you can forfeit or not")
    template: NpcTemplateModel
    monsters: Sequence[PartyMemberModel] = Field(
        [], description="List of monsters in the NPCs party"
    )
    items: Sequence[BagItemModel] = Field(
        [], description="List of items in the NPCs bag"
    )


class BattleHudModel(BaseModel):
    hud_player: str = Field(
        ..., description="Sprite used for hud player background"
    )
    hud_opponent: str = Field(
        ..., description="Sprite used for hud opponent background"
    )
    tray_player: str = Field(
        ..., description="Sprite used for tray player background"
    )
    tray_opponent: str = Field(
        ..., description="Sprite used for tray opponent background"
    )
    hp_bar_player: bool = Field(
        True, description="Whether draw or not player HP Bar"
    )
    hp_bar_opponent: bool = Field(
        True, description="Whether draw or not opponent HP Bar"
    )
    exp_bar_player: bool = Field(
        True, description="Whether draw or not player EXP Bar"
    )

    @field_validator(
        "hud_player",
        "hud_opponent",
        "tray_player",
        "tray_opponent",
    )
    def file_exists(cls: BattleHudModel, v: str) -> str:
        if has.file(v):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class BattleIconsModel(BaseModel):
    icon_alive: str = Field(
        ..., description="Sprite used for icon (small tuxeball) monster alive"
    )
    icon_status: str = Field(
        ...,
        description="Sprite used for icon (small tuxeball) monster affected",
    )
    icon_faint: str = Field(
        ...,
        description="Sprite used for icon (small tuxeball) monster fainted",
    )
    icon_empty: str = Field(
        ...,
        description="Sprite used for icon (small tuxeball) empty slot",
    )

    @field_validator(
        "icon_alive",
        "icon_faint",
        "icon_status",
        "icon_empty",
    )
    def file_exists(cls: BattleIconsModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.ICON_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class BattleGraphicsModel(BaseModel):
    menu: str = Field(
        "MainCombatMenuState", description="Menu used for combat."
    )
    msgid: str = Field(
        "combat_monster_choice",
        description="msgid of the sentence that is going to appear in the "
        "combat menu in between the rounds, when the monster needs to choose "
        "the next move, (name) shows monster name, (player) the player name.",
    )
    island_back: str = Field(..., description="Sprite used for back combat")
    island_front: str = Field(..., description="Sprite used for front combat")
    background: str = Field(..., description="Sprite used for background")
    hud: BattleHudModel
    icons: BattleIconsModel

    @field_validator("island_back", "island_front")
    def island_exists(cls: BattleGraphicsModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.ISLAND_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {v}")

    @field_validator("background")
    def background_exists(cls: BattleGraphicsModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.BATTLE_BG_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {v}")

    @field_validator("msgid")
    def translation_exists_msgid(cls: BattleGraphicsModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("menu")
    def check_state(cls: BattleGraphicsModel, v: str) -> str:
        states = [state.name for state in State]
        if v in states:
            return v
        raise ValueError(f"state isn't among: {states}")


class EnvironmentModel(BaseModel):
    slug: str = Field(..., description="Slug of the name of the environment")
    battle_music: str = Field(
        ..., description="Filename of the music to use for this environment"
    )
    battle_graphics: BattleGraphicsModel

    @field_validator("battle_music")
    def battle_music_exists(cls: EnvironmentModel, v: str) -> str:
        if has.db_entry("music", v):
            return v
        raise ValueError(f"the music {v} doesn't exist in the db")


class EncounterItemModel(BaseModel):
    monster: str = Field(..., description="Monster slug for this encounter")
    encounter_rate: float = Field(
        ..., description="Probability of encountering this monster."
    )
    level_range: Sequence[int] = Field(
        ...,
        description="Minimum and maximum levels at which this encounter can occur.",
        max_length=2,
    )
    variables: Optional[Sequence[str]] = Field(
        None,
        description="List of variables that affect the encounter.",
        min_length=1,
    )
    exp_req_mod: int = Field(
        1,
        description="Modifier for the experience points required to defeat this wild monster.",
        gt=0,
    )

    @field_validator("monster")
    def monster_exists(cls: EncounterItemModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")

    @field_validator("variables")
    def variable_exists(
        cls: EncounterItemModel, v: Optional[str]
    ) -> Optional[str]:
        if v is None:
            return v
        if len(v) != len(set(v)):
            raise ValueError("The sequence contains duplicate variables")
        for variable in v:
            if (
                not variable
                or len(variable.split(":")) != 2
                or variable[0] == ":"
                or variable[-1] == ":"
            ):
                raise ValueError(
                    f"the variable {variable} isn't formatted correctly"
                )
        return v


class EncounterModel(BaseModel):
    slug: str = Field(
        ..., description="Slug to uniquely identify this encounter"
    )
    monsters: Sequence[EncounterItemModel] = Field(
        [], description="Monsters encounterable"
    )


class DialogueModel(BaseModel):
    slug: str = Field(
        ..., description="Slug to uniquely identify this dialogue"
    )
    bg_color: str = Field(..., description="RGB color (eg. 255:0:0)")
    font_color: str = Field(..., description="RGB color (eg. 255:0:0)")
    font_shadow_color: str = Field(..., description="RGB color (eg. 255:0:0)")
    border_slug: str = Field(..., description="Name of the border")
    border_path: str = Field(..., description="Path to the border")

    # Validate resources that should exist
    @field_validator("border_slug")
    def file_exists(cls: DialogueModel, v: str) -> str:
        file: str = f"gfx/borders/{v}.png"
        if has.file(file) and has.size(file, prepare.BORDERS_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {file}")


class ElementItemModel(BaseModel):
    against: ElementType = Field(..., description="Name of the type")
    multiplier: float = Field(1.0, description="Multiplier against the type")


class ElementModel(BaseModel):
    slug: ElementType = Field(
        ..., description="Slug uniquely identifying the type"
    )
    icon: str = Field(..., description="The icon to use for the type")
    types: Sequence[ElementItemModel]

    @field_validator("slug")
    def translation_exists_element(
        cls: ElementModel, v: ElementType
    ) -> ElementType:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("icon")
    def file_exists(cls: ElementModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.ELEMENT_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")


class EconomyItemModel(BaseModel):
    item_name: str = Field(..., description="Name of the item")
    price: int = Field(0, description="Price of the item")
    cost: int = Field(0, description="Cost of the item")
    inventory: int = Field(-1, description="Quantity of the item")
    variable: Optional[str] = Field(None, description="Variable of the item")

    @field_validator("item_name")
    def item_exists(cls: EconomyItemModel, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")

    @field_validator("variable")
    def variable_exists(
        cls: EconomyItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or v.find(":") > 1:
            return v
        raise ValueError(f"the variable {v} isn't formatted correctly")


class EconomyModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the economy")
    items: Sequence[EconomyItemModel]


class TemplateModel(BaseModel):
    slug: str = Field(
        ..., description="Slug uniquely identifying the template"
    )
    double: bool = Field(False, description="Whether triggers 2vs2 or not")


class MissionModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the mission")

    @field_validator("slug")
    def translation_exists_mission(cls: MissionModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class MusicModel(BaseModel):
    slug: str = Field(..., description="Unique slug for the music")
    file: str = Field(..., description="File for the music")

    @field_validator("file")
    def file_exists(cls: MusicModel, v: str) -> str:
        file: str = f"music/{v}"
        if has.file(file):
            return v
        raise ValueError(f"the music {v} doesn't exist in the db")


class SoundModel(BaseModel):
    slug: str = Field(..., description="Unique slug for the sound")
    file: str = Field(..., description="File for the sound")

    @field_validator("file")
    def file_exists(cls: SoundModel, v: str) -> str:
        file: str = f"sounds/{v}"
        if has.file(file):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class AnimationModel(BaseModel):
    slug: str = Field(..., description="Unique slug for the animation")
    file: str = Field(..., description="File of the animation")

    @field_validator("file")
    def file_exists(cls: AnimationModel, v: str, info: ValidationInfo) -> str:
        slug = info.data.get("slug")
        file: str = f"animations/{v}/{slug}_00.png"
        if has.file(file):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")


TableName = Literal[
    "economy",
    "element",
    "shape",
    "template",
    "mission",
    "encounter",
    "dialogue",
    "environment",
    "item",
    "monster",
    "music",
    "animation",
    "npc",
    "sounds",
    "condition",
    "technique",
]

DataModel = Union[
    EconomyModel,
    ElementModel,
    ShapeModel,
    TemplateModel,
    MissionModel,
    EncounterModel,
    DialogueModel,
    EnvironmentModel,
    ItemModel,
    MonsterModel,
    MusicModel,
    AnimationModel,
    NpcModel,
    SoundModel,
    ConditionModel,
    TechniqueModel,
]


class JSONDatabase:
    """
    Handles connecting to the game database for resources.

    Examples of such resources include monsters, stats, etc.

    """

    def __init__(self, dir: str = "all") -> None:
        self._tables: list[TableName] = [
            "item",
            "monster",
            "npc",
            "condition",
            "technique",
            "encounter",
            "dialogue",
            "environment",
            "sounds",
            "music",
            "animation",
            "economy",
            "element",
            "shape",
            "template",
            "mission",
        ]
        self.preloaded: dict[TableName, dict[str, Any]] = {}
        self.database: dict[TableName, dict[str, Any]] = {}
        self.path = ""
        for table in self._tables:
            self.preloaded[table] = {}
            self.database[table] = {}

        # self.load(dir)

    def preload(
        self, directory: Union[TableName, Literal["all"]] = "all"
    ) -> None:
        """
        Loads all data from JSON files located under our data path as an
        untyped preloaded dictionary.

        Parameters:
            directory: The directory under mods/tuxemon/db/ to load. Defaults
                to "all".

        """
        if directory == "all":
            for table in self._tables:
                self.load_json(table)
        else:
            self.load_json(directory)

    def load(
        self,
        directory: Union[TableName, Literal["all"]] = "all",
        validate: bool = False,
    ) -> None:
        """
        Loads all data from JSON files located under our data path.

        Parameters:
            directory: The directory under mods/tuxemon/db/ to load. Defaults
                to "all".
            validate: Whether or not we should raise an exception if validation
                fails

        """
        self.preload(directory)
        for table, entries in self.preloaded.items():
            for slug, item in entries.items():
                self.load_model(item, table, validate)
        self.preloaded.clear()

    def _load_json_files(self, directory: TableName) -> None:
        for json_item in os.listdir(os.path.join(self.path, directory)):
            # Only load .json files.
            if not json_item.endswith(".json"):
                continue

            # Load our json as a dictionary.
            with open(os.path.join(self.path, directory, json_item)) as fp:
                try:
                    item = json.load(fp)
                except ValueError as e:
                    logger.error(f"Invalid JSON {json_item}: {e}")
                    continue

            if type(item) is list:
                for sub in item:
                    self.load_dict(
                        sub, directory, os.path.join(self.path, directory)
                    )
            else:
                self.load_dict(
                    item, directory, os.path.join(self.path, directory)
                )

    def load_json(self, directory: TableName, validate: bool = False) -> None:
        """
        Loads all JSON items under a specified path.

        Parameters:
            directory: The directory under mods/mod_name/db/ to look in.
            validate: Whether or not we should raise an exception if validation
                fails

        """
        for mod_directory in prepare.CONFIG.mods:
            self.path = os.path.join(paths.mods_folder, mod_directory, "db")
            if os.path.exists(self.path) and os.path.exists(
                os.path.join(self.path, directory)
            ):
                self._load_json_files(directory)

    def load_dict(
        self, item: Mapping[str, Any], table: TableName, path: str
    ) -> None:
        """
        Loads a single json object and adds it to the appropriate preload db
        table.

        Parameters:
            item: The json object to load in.
            table: The db table to load the object into.
            path: The path from which the item was loaded.

        """
        if item["slug"] in self.preloaded[table]:
            if path in self.preloaded[table][item["slug"]].get("paths", []):
                logger.warning(
                    f"Error: Item with slug {item['slug']} was already loaded from this path ({path}).",
                )
                return
            else:
                self.preloaded[table][item["slug"]]["paths"].append(path)
        else:
            self.preloaded[table][item["slug"]] = item
            self.preloaded[table][item["slug"]]["paths"] = [path]

    def load_model(
        self, item: Mapping[str, Any], table: TableName, validate: bool = False
    ) -> None:
        """
        Loads a single json object, casts it to the appropriate data model,
        and adds it to the appropriate db table.

        Parameters:
            item: The json object to load in.
            table: The db table to load the object into.
            validate: Whether or not we should raise an exception if validation
                fails

        """
        if item["slug"] in self.database[table]:
            logger.warning(
                "Error: Item with slug %s was already loaded.",
                item,
            )
            return

        try:
            if table == "economy":
                economy = EconomyModel(**item)
                self.database[table][economy.slug] = economy
            elif table == "element":
                element = ElementModel(**item)
                self.database[table][element.slug] = element
            elif table == "shape":
                shape = ShapeModel(**item)
                self.database[table][shape.slug] = shape
            elif table == "template":
                template = TemplateModel(**item)
                self.database[table][template.slug] = template
            elif table == "mission":
                mission = MissionModel(**item)
                self.database[table][mission.slug] = mission
            elif table == "encounter":
                encounter = EncounterModel(**item)
                self.database[table][encounter.slug] = encounter
            elif table == "dialogue":
                dialogue = DialogueModel(**item)
                self.database[table][dialogue.slug] = dialogue
            elif table == "environment":
                env = EnvironmentModel(**item)
                self.database[table][env.slug] = env
            elif table == "item":
                itm = ItemModel(**item)
                self.database[table][itm.slug] = itm
            elif table == "monster":
                mon = MonsterModel(**item)
                self.database[table][mon.slug] = mon
            elif table == "music":
                music = MusicModel(**item)
                self.database[table][music.slug] = music
            elif table == "animation":
                animation = AnimationModel(**item)
                self.database[table][animation.slug] = animation
            elif table == "npc":
                npc = NpcModel(**item)
                self.database[table][npc.slug] = npc
            elif table == "sounds":
                sfx = SoundModel(**item)
                self.database[table][sfx.slug] = sfx
            elif table == "condition":
                cond = ConditionModel(**item)
                self.database[table][cond.slug] = cond
            elif table == "technique":
                teq = TechniqueModel(**item)
                self.database[table][teq.slug] = teq
            else:
                raise ValueError(f"Unexpected {table =}")
        except (ValidationError, ValueError) as e:
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
    def lookup(self, slug: str, table: Literal["condition"]) -> ConditionModel:
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
    def lookup(self, slug: str, table: Literal["dialogue"]) -> DialogueModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["economy"]) -> EconomyModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["element"]) -> ElementModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["shape"]) -> ShapeModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["template"]) -> TemplateModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["mission"]) -> MissionModel:
        pass

    @overload
    def lookup(
        self,
        slug: str,
        table: Literal["music"],
    ) -> MusicModel:
        pass

    @overload
    def lookup(
        self,
        slug: str,
        table: Literal["animation"],
    ) -> AnimationModel:
        pass

    @overload
    def lookup(
        self,
        slug: str,
        table: Literal["sounds"],
    ) -> SoundModel:
        pass

    @overload
    def lookup(
        self,
        slug: str,
        table: Literal["environment"],
    ) -> EnvironmentModel:
        pass

    def lookup(self, slug: str, table: TableName) -> DataModel:
        """
        Looks up a monster, technique, item, npc, etc based on slug.

        Parameters:
            slug: The slug of the monster, technique, item, or npc.  A short
                English identifier.
            table: Which index to do the search in.

        Returns:
            A pydantic.BaseModel from the resulting lookup.

        """
        table_entry = self.database[table]
        if not table_entry:
            logger.exception(f"{table} table wasn't loaded")
            sys.exit()
        if slug not in table_entry:
            self.log_missing_entry_and_exit(table, slug)
        else:
            return table_entry[slug]

    def lookup_file(self, table: TableName, slug: str) -> str:
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

        filename = self.database[table][slug].file or slug
        if filename == slug:
            logger.debug(
                f"Could not find a file record for slug {slug}, did you remember to create a database record?"
            )

        return filename

    def has_entry(self, slug: str, table: TableName) -> bool:
        table_entry = self.database[table]
        if not table_entry:
            logger.exception(f"{table} table wasn't loaded")
            sys.exit()
        return slug in table_entry

    def log_missing_entry_and_exit(
        self,
        table: Literal[
            "economy",
            "element",
            "shape",
            "template",
            "mission",
            "encounter",
            "dialogue",
            "environment",
            "item",
            "monster",
            "music",
            "animation",
            "npc",
            "sounds",
            "condition",
            "technique",
        ],
        slug: str,
    ) -> None:
        options = difflib.get_close_matches(slug, self.database[table].keys())
        options = [repr(s) for s in options]
        if len(options) >= 2:
            options_string = ", ".join(
                (*options[:-2], options[-2] + " or " + options[-1])
            )
            hint = f"Did you mean {options_string}?"
        elif len(options) == 1:
            options_string = options[0]
            hint = f"Did you mean {options_string}?"
        else:
            hint = "No similar slugs. Are you sure it's in the DB?"
        logger.exception(f"Lookup failed for unknown {table} '{slug}'. {hint}")
        sys.exit()


class Validator:
    """
    Helper class for validating resources exist.

    """

    def __init__(self) -> None:
        self.db = JSONDatabase()
        self.db.preload()

    def translation(self, msgid: str) -> bool:
        """
        Check to see if a translation exists for the given slug

        Parameters:
            msgid: The slug of the text to translate. A short English
                identifier.

        Returns:
            True if translation exists

        """
        return T.translate(msgid) != msgid

    def file(self, file: str) -> bool:
        """
        Check to see if a given file exists

        Parameters:
            file: The file path relative to a mod directory

        Returns:
            True if file exists

        """

        try:
            path = prepare.fetch(file)
            return os.path.exists(path)
        except OSError:
            return False

    def size(self, file: str, size: tuple[int, int]) -> bool:
        """
        Check to see if a given file respects the predefined size.

        Parameters:
            file: The file path relative to a mod directory
            size: The predefined size

        Returns:
            True if file respects

        """
        path = prepare.fetch(file)
        sprite = Image.open(path)
        native = prepare.NATIVE_RESOLUTION
        if size == native:
            if sprite.size[0] > size[0] or sprite.size[1] > size[1]:
                sprite.close()
                raise ValueError(
                    f"{file} {sprite.size}: "
                    f"It must be less than the native resolution {native}"
                )
        else:
            if sprite.size[0] != size[0] or sprite.size[1] != size[1]:
                sprite.close()
                raise ValueError(
                    f"{file} {sprite.size}: It must be equal to {size}"
                )
        sprite.close()
        return True

    def check_conditions(self, conditions: Sequence[str]) -> bool:
        """
        Check to see if a condition is correctly formatted.

        Parameters:
            conditions: The sequence containing the conditions

        Returns:
            True if it's correctly formatted

        """
        if not conditions:
            return True

        _conditions = [
            element
            for condition in conditions
            for element in condition.split(" ")
        ]

        # check nr of elements
        if len(_conditions) == 1:
            raise ValueError(
                f"{_conditions} invalid, it must have at least: 'is' + 'condition'"
            )

        # check prefix
        prefix = _conditions[0]
        _prefix = True if prefix == "is" or _conditions[0] == "not" else False
        if not _prefix:
            raise ValueError(f"{prefix} is invalid, it must be: 'is' or 'not'")

        return True

    def db_entry(self, table: TableName, slug: str) -> bool:
        """
        Check to see if the given slug exists in the database for the given
        table.

        Parameters:
            slug: The slug of the monster, technique, item, or npc.  A short
                English identifier.
            table: Which index to do the search in. Can be: "monster",
                "item", "npc", or "technique".

        Returns:
            True if entry exists

        """

        if slug in self.db.preloaded[table]:
            return True
        return False


# Validator container
has = Validator()

# Global database container
db = JSONDatabase()
