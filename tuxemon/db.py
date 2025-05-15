# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import difflib
import json
import logging
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from typing import Annotated, Any, Literal, Optional, Union, overload

import yaml
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
from tuxemon.constants.paths import mods_folder
from tuxemon.formula import config_monster
from tuxemon.locale import T
from tuxemon.surfanim import FlipAxes

logger = logging.getLogger(__name__)

# Load the default translator for data validation
T.collect_languages(False)
T.load_translator()


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
    potion = "potion"
    utility = "utility"
    quest = "quest"


class PlagueType(str, Enum):
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


class ItemCategory(str, Enum):
    none = "none"
    badge = "badge"
    elements = "elements"
    fossil = "fossil"
    morph = "morph"
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


class SeenStatus(str, Enum):
    unseen = "unseen"
    seen = "seen"
    caught = "caught"


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
    removed = "removed"


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


class TargetType(str, Enum):
    enemy_monster = "enemy_monster"
    own_monster = "own_monster"
    enemy_team = "enemy_team"
    own_team = "own_team"
    enemy_trainer = "enemy_trainer"
    own_trainer = "own_trainer"


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


class CommonCondition(BaseModel):
    type: str = Field(..., description="The name of the condition")
    parameters: Sequence[str] = Field(
        [], description="The parameters that must be met"
    )
    operator: str = Field(..., description="The operator 'is' or 'not'.")

    @field_validator("operator")
    def operator_must_be_is_or_not(cls: CommonCondition, v: str) -> str:
        if v not in ["is", "not"]:
            raise ValueError('operator must be either "is" or "not"')
        return v


class CommonEffect(BaseModel):
    type: str = Field(..., description="The name of the condition")
    parameters: Sequence[str] = Field(
        [], description="The parameters that must be met"
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
    holdable: bool = Field(
        False, description="Whether or not this item is holdable."
    )
    resellable: bool = Field(
        False, description="Whether or not this item is resellable."
    )


class WorldMenuEntry(BaseModel):
    position: int
    label_key: str
    state: str


class ItemModel(BaseModel):
    model_config = ConfigDict(title="Item")
    slug: str = Field(..., description="The slug of the item")
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
    conditions: Sequence[CommonCondition] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[CommonEffect] = Field(
        ..., description="Effects this item will have"
    )
    flip_axes: FlipAxes = Field(
        FlipAxes.NONE,
        description="Axes along which item animation should be flipped",
    )
    animation: Optional[str] = Field(
        None, description="Animation to play for this item"
    )
    world_menu: Optional[WorldMenuEntry] = Field(
        None,
        description="Item adds to World Menu a button (position, label -inside the PO -,state, eg. 3:nu_phone:PhoneState)",
    )
    cost: int = Field(0, description="The standard cost of the item.", ge=0)
    modifiers: list[Modifier] = Field(..., description="Various modifiers")

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


class AttributesModel(BaseModel):
    armour: int = Field(..., description="Armour value")
    dodge: int = Field(..., description="Dodge value")
    hp: int = Field(..., description="HP (Hit Points) value")
    melee: int = Field(..., description="Melee value")
    ranged: int = Field(..., description="Ranged value")
    speed: int = Field(..., description="Speed value")


class ShapeModel(BaseModel):
    slug: str = Field(
        ..., description="Slug of the shape, used as a unique identifier."
    )
    attributes: AttributesModel = Field(
        ..., description="Statistical attributes of the shape."
    )

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
    element: Optional[str] = Field(
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
    inside: Optional[bool] = Field(
        None,
        description="Whether the monster must be inside to evolve.",
    )
    traded: Optional[bool] = Field(
        None,
        description="Whether the monster must have been traded to evolve.",
    )
    variables: Sequence[dict[str, str]] = Field(
        [],
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
    moves: Sequence[str] = Field(
        [],
        description="The techniques that the monster must have learned for the evolution to occur.",
        min_length=1,
        max_length=prepare.MAX_MOVES,
    )
    bond: Optional[str] = Field(
        None,
        description="The bond value comparison required for the monster to evolve (e.g., greater_than, less_than, etc.).",
    )
    party: Sequence[str] = Field(
        [],
        description="The slug of the monsters that must be in the party for the evolution to occur.",
        min_length=1,
        max_length=prepare.PARTY_LIMIT - 1,
    )
    taste_cold: Optional[str] = Field(
        None,
        description="The required taste cold value for the monster to evolve.",
    )
    taste_warm: Optional[str] = Field(
        None,
        description="The required taste warm value for the monster to evolve.",
    )

    @field_validator("moves")
    def move_exists(
        cls: MonsterEvolutionItemModel, v: Sequence[str]
    ) -> Sequence[str]:
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

    @field_validator("taste_cold", "taste_warm")
    def taste_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.db_entry("taste", v):
            return v
        raise ValueError(f"the taste {v} doesn't exist in the db")

    @field_validator("element")
    def element_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.db_entry("element", v):
            return v
        raise ValueError(f"the element {v} doesn't exist in the db")

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
            lower, upper = config_monster.bond_range
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
    terrains: Sequence[str] = Field(
        ..., description="The terrains of the monster"
    )
    types: Sequence[str] = Field([], description="The type(s) of this monster")
    shape: str = Field(..., description="The shape of the monster")
    tags: Sequence[str] = Field(..., description="The tags of the monster")
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

    @field_validator("types")
    def element_exists(
        cls: MonsterModel, elements: Sequence[str]
    ) -> Sequence[str]:
        if not elements:
            return elements

        invalid_elements = [
            element
            for element in elements
            if not has.db_entry("element", element)
        ]
        if invalid_elements:
            raise ValueError(
                f"elements {', '.join(invalid_elements)} don't exist in the db"
            )

        return elements

    @field_validator("shape")
    def shape_exists(cls: MonsterModel, v: str) -> str:
        if has.db_entry("shape", v):
            return v
        raise ValueError(f"the shape {v} doesn't exist in the db")

    @field_validator("terrains")
    def terrain_exists(cls: MonsterModel, v: Sequence[str]) -> Sequence[str]:
        if v:
            for terrain in v:
                if not has.db_entry("terrain", terrain):
                    raise ValueError(
                        f"the terrain '{terrain}' doesn't exist in the db"
                    )
        return v


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


class Modifier(BaseModel):
    attribute: str = Field(
        ..., description="Attribute being modified (type, etc.)"
    )
    values: Sequence[str] = Field(
        [],
        description="Values associated with the modification (eg. fire, etc.)",
    )
    multiplier: float = Field(1.0, description="Multiplier", ge=0.0, le=2.0)


class TechSort(str, Enum):
    damage = "damage"
    meta = "meta"


class CategoryStatus(str, Enum):
    negative = "negative"
    positive = "positive"
    neutral = "neutral"


class ResponseStatus(str, Enum):
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
    category: TechCategory = Field(
        ...,
        description="The tags of the technique",
    )
    tags: Sequence[str] = Field(
        ..., description="The tags of the technique", min_length=1
    )
    conditions: Sequence[CommonCondition] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[CommonEffect] = Field(
        ..., description="Effects this technique uses"
    )
    flip_axes: FlipAxes = Field(
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
    modifiers: list[Modifier] = Field(..., description="Various modifiers")

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
    types: Sequence[str] = Field([], description="Type(s) of the technique")
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

    @field_validator("sfx")
    def sfx_tech_exists(cls: TechniqueModel, v: str) -> str:
        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")

    @field_validator("types")
    def element_exists(
        cls: TechniqueModel, elements: Sequence[str]
    ) -> Sequence[str]:
        if not elements:
            return elements

        invalid_elements = [
            element
            for element in elements
            if not has.db_entry("element", element)
        ]
        if invalid_elements:
            raise ValueError(
                f"elements {', '.join(invalid_elements)} don't exist in the db"
            )

        return elements


class StatusModel(BaseModel):
    slug: str = Field(..., description="The slug of the status")
    sort: TechSort = Field(..., description="The sort of status this is")
    icon: str = Field(..., description="The icon to use for the condition")
    conditions: Sequence[CommonCondition] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[CommonEffect] = Field(
        ..., description="Effects this status uses"
    )
    flip_axes: FlipAxes = Field(
        ...,
        description="Axes along which status animation should be flipped",
    )
    animation: Optional[str] = Field(
        None, description="Animation to play for this status"
    )
    sfx: str = Field(
        ..., description="Sound effect to play when this status is used"
    )
    bond: bool = Field(
        False,
        description="Whether or not there is a bond between attacker and defender",
    )
    duration: int = Field(
        0, description="How many turns the status is supposed to last"
    )
    modifiers: list[Modifier] = Field(..., description="Various modifiers")

    # Optional fields
    category: Optional[CategoryStatus] = Field(
        None, description="Category status: positive or negative"
    )
    repl_pos: Optional[ResponseStatus] = Field(
        None, description="How to reply to a positive status"
    )
    repl_neg: Optional[ResponseStatus] = Field(
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
        description="Slug of what string to display when status is gained",
    )
    use_success: Optional[str] = Field(
        None,
        description="Slug of what string to display when status succeeds",
    )
    use_failure: Optional[str] = Field(
        None,
        description="Slug of what string to display when status fails",
    )
    range: Range = Field(..., description="The attack range of this status")
    cond_id: int = Field(..., description="The id of this status")
    statspeed: Optional[StatModel] = Field(None)
    stathp: Optional[StatModel] = Field(None)
    statarmour: Optional[StatModel] = Field(None)
    statdodge: Optional[StatModel] = Field(None)
    statmelee: Optional[StatModel] = Field(None)
    statranged: Optional[StatModel] = Field(None)

    # Validate resources that should exist
    @field_validator("icon")
    def file_exists(cls: StatusModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.STATUS_ICON_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")

    # Validate fields that refer to translated text
    @field_validator("gain_cond", "use_success", "use_failure")
    def translation_exists(
        cls: StatusModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_cond(cls: StatusModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("animation")
    def animation_exists(cls: StatusModel, v: Optional[str]) -> Optional[str]:
        file: str = f"animations/technique/{v}_00.png"
        if (
            not v
            or has.db_entry("animation", v)
            and has.size(file, prepare.NATIVE_RESOLUTION)
        ):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")

    @field_validator("repl_tech", "repl_item")
    def status_exists(cls: StatusModel, v: Optional[str]) -> Optional[str]:
        if not v or has.db_entry("status", v) or has.db_entry("technique", v):
            return v
        raise ValueError(f"the status {v} doesn't exist in the db")

    @field_validator("sfx")
    def sfx_cond_exists(cls: StatusModel, v: str) -> str:
        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class PartyMemberModel(BaseModel):
    slug: str = Field(..., description="Slug of the monster")
    level: int = Field(..., description="Level of the monster", gt=0)
    money_mod: float = Field(
        ..., description="Modifier for money this monster gives", gt=0
    )
    exp_req_mod: float = Field(
        ..., description="Experience required modifier", gt=0
    )
    gender: GenderType = Field(..., description="Gender of the monster")
    variables: Sequence[dict[str, str]] = Field(
        [],
        description="Sequence of variables that affect the presence of the monster.",
        min_length=1,
    )

    @field_validator("slug")
    def monster_exists(cls: PartyMemberModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class BagItemModel(BaseModel):
    slug: str = Field(..., description="Slug of the item")
    quantity: int = Field(..., description="Quantity of the item")
    variables: Sequence[dict[str, str]] = Field(
        [],
        description="List of variables that affect the item.",
        min_length=1,
    )

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
    held_items: Sequence[str] = Field(
        ..., description="A list of items that will be held."
    )
    level_range: Sequence[int] = Field(
        ...,
        description="Minimum and maximum levels at which this encounter can occur.",
        max_length=2,
    )
    variables: Sequence[dict[str, str]] = Field(
        ...,
        description="List of variables that affect the encounter.",
    )
    exp_req_mod: float = Field(
        ...,
        description="Modifier for the experience points required to defeat this wild monster.",
        gt=0.0,
    )

    @field_validator("monster")
    def monster_exists(cls: EncounterItemModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")

    @field_validator("held_items")
    def item_exists(
        cls: EncounterItemModel, v: Sequence[str]
    ) -> Sequence[str]:
        if v:
            for item in v:
                if not has.db_entry("item", item):
                    raise ValueError(
                        f"the item '{item}' doesn't exist in the db"
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
    against: str = Field(..., description="Name of the type")
    multiplier: float = Field(1.0, description="Multiplier against the type")

    @field_validator("against")
    def element_exists(cls: ElementItemModel, v: str) -> str:
        if not v or has.db_entry("element", v):
            return v
        raise ValueError(f"the element {v} doesn't exist in the db")


class ElementModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the type")
    icon: str = Field(..., description="The icon to use for the type")
    types: Sequence[ElementItemModel]

    @field_validator("slug")
    def translation_exists_element(cls: ElementModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("icon")
    def file_exists(cls: ElementModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.ELEMENT_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")


class TasteModel(BaseModel):
    slug: str = Field(..., description="Slug of the taste")
    name: str = Field(..., description="Name of the taste")
    taste_type: Literal["warm", "cold"] = Field(
        ..., description="Type of taste: 'cold' or 'warm'"
    )
    modifiers: Sequence[Modifier] = Field(
        ..., description="Modifiers associated with the taste"
    )

    @field_validator("name")
    def translation_exists_taste(cls: TasteModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class EconomyEntityModel(BaseModel):
    price: int = Field(0, description="Price of the entity")
    cost: int = Field(0, description="Cost of the entity")
    inventory: int = Field(-1, description="Quantity of the entity")
    variables: Sequence[dict[str, str]] = Field(
        [],
        description="List of variables that affect the entity in the economy.",
        min_length=1,
    )


class EconomyItemModel(EconomyEntityModel):
    name: str = Field(..., description="Name of the entity")
    inventory: int = Field(-1, description="Quantity of the entity")

    @field_validator("name")
    def item_exists(cls: EconomyEntityModel, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")


class EconomyMonsterModel(EconomyEntityModel):
    name: str = Field(..., description="Name of the entity")
    inventory: int = Field(1, description="Quantity of the entity", gt=0)
    level: int = Field(1, description="Level of the entity", gt=0)

    @field_validator("name")
    def monster_exists(cls: EconomyEntityModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class EconomyModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the economy")
    resale_multiplier: float = Field(..., description="Resale multiplier")
    background: str = Field(..., description="Sprite used for background")
    items: Sequence[EconomyItemModel]
    monsters: Sequence[EconomyMonsterModel]

    @field_validator("background")
    def background_exists(cls: EconomyModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.NATIVE_RESOLUTION):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class TemplateModel(BaseModel):
    slug: str = Field(
        ..., description="Slug uniquely identifying the template"
    )


class ProgressModel(BaseModel):
    game_variables: dict[str, Any] = Field(
        ...,
        description="Dictionary of game variables tracking the mission's progress",
    )
    completion_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of mission completed"
    )


class MissionModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the mission")
    description: str = Field(
        ..., description="Detailed description of the mission objectives"
    )
    prerequisites: Sequence[dict[str, Any]] = Field(
        ...,
        description="List of prerequisite missions and their game variables",
    )
    connected_missions: Sequence[dict[str, Any]] = Field(
        ...,
        description="List of missions accessible once this mission is complete",
    )
    progress: Sequence[ProgressModel] = Field(
        ..., description="List of progress tracking entries for the mission"
    )
    required_items: Sequence[str] = Field(
        ..., description="List of items required to start the mission"
    )
    required_monsters: Sequence[str] = Field(
        ..., description="List of monsters required to start the mission"
    )
    required_missions: Sequence[str] = Field(
        ...,
        description="List of mission slugs that must be completed before this mission",
    )

    @field_validator("slug")
    def translation_exists_mission(cls: MissionModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("description")
    def translation_exists_desc(cls: MissionModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("required_items")
    def item_exists(cls: MissionModel, v: Sequence[str]) -> Sequence[str]:
        for item_slug in v:
            if not has.db_entry("item", item_slug):
                raise ValueError(
                    f"The item '{item_slug}' doesn't exist in the db"
                )
        return v

    @field_validator("required_monsters")
    def monster_exists(cls: MissionModel, v: Sequence[str]) -> Sequence[str]:
        for monster_slug in v:
            if not has.db_entry("monster", monster_slug):
                raise ValueError(
                    f"The monster '{monster_slug}' doesn't exist in the db"
                )
        return v


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


class TerrainModel(BaseModel):
    slug: str = Field(..., description="Slug of the terrain")
    name: str = Field(..., description="Name of the terrain condition")
    element_modifier: dict[str, float] = Field(
        ..., description="Modifiers for elemental techniques in this terrain"
    )

    @field_validator("name")
    def translation_exists_item(cls: TerrainModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class WeatherModel(BaseModel):
    slug: str = Field(..., description="Slug of the weather")
    name: str = Field(..., description="Name of the weather condition")
    element_modifier: dict[str, float] = Field(
        ...,
        description="Modifiers for elemental techniques during this weather",
    )

    @field_validator("name")
    def translation_exists_item(cls: WeatherModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


TableName = Literal[
    "economy",
    "element",
    "taste",
    "shape",
    "terrain",
    "weather",
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
    "status",
    "technique",
]

DataModel = Union[
    EconomyModel,
    ElementModel,
    TasteModel,
    ShapeModel,
    TerrainModel,
    WeatherModel,
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
    StatusModel,
    TechniqueModel,
]


def load_model_map(
    model_map_config: dict[TableName, str],
) -> dict[TableName, type[DataModel]]:
    model_map: dict[TableName, type[DataModel]] = {}
    for table, model_path in model_map_config.items():
        module_name, class_name = model_path.rsplit(".", 1)
        module = import_module(module_name)
        model_map[table] = getattr(module, class_name)
    return model_map


@dataclass
class DatabaseConfig:
    model_map: dict[TableName, str]
    mod_base_path: str
    mod_db_subfolder: str
    file_extensions: list[str]
    default_lookup_table: TableName
    active_mods: list[str]
    mod_versions: dict[str, str]
    mod_table_exclusions: dict[str, list[str]]
    mod_activation: dict[str, bool]
    mod_tables: dict[str, list[TableName]]
    mod_dependencies: dict[str, list[str]]


class EntryNotFoundError(Exception):
    pass


class DependencyResolver:
    def __init__(self, mod_dependencies: dict[str, list[str]]) -> None:
        self.mod_dependencies = mod_dependencies

    def resolve(
        self, mod: str, visited: Optional[set[str]] = None
    ) -> list[str]:
        if visited is None:
            visited = set()
        if mod in visited:
            return []
        visited.add(mod)
        dependencies = []
        if mod in self.mod_dependencies:
            for dep in self.mod_dependencies[mod]:
                dependencies.extend(self.resolve(dep, visited))
                dependencies.append(dep)
        return list(dict.fromkeys(dependencies))


class ModMetadataLoader:
    def __init__(
        self, active_mods: list[str], base_path: str = "mods"
    ) -> None:
        self.active_mods = active_mods
        self.base_path = base_path

    def load_metadata(self) -> dict[str, dict[str, Any]]:
        metadata = {}
        for mod_directory in self.active_mods:
            mod_path = os.path.join(self.base_path, mod_directory, "mod.json")
            if os.path.exists(mod_path):
                try:
                    with open(mod_path) as f:
                        metadata[mod_directory] = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Error loading metadata for '{mod_directory}': {e}"
                    )
            else:
                logger.error(f"Metadata file missing: '{mod_path}'")
        return metadata


class ModelLoader:
    def __init__(self, model_map: dict[TableName, type[DataModel]]):
        self.model_map = model_map

    def validate(self, item: Mapping[str, Any], table: TableName) -> DataModel:
        try:
            model_class = self.model_map.get(table)
            if model_class:
                return model_class(**item)
            else:
                raise ValueError(f"Unexpected table: {table}")
        except ValidationError as e:
            logger.error(
                f"Validation failed for '{item['slug']}' in table '{table}': {e}"
            )
            raise e

    def load(
        self, item: Mapping[str, Any], table: TableName, validate: bool = False
    ) -> DataModel:
        try:
            if validate:
                return self.validate(item, table)
            else:
                model_class = self.model_map.get(table)
                if model_class:
                    return model_class(**item)
                else:
                    raise ValueError(f"Unexpected table: {table}")
        except ValidationError as e:
            logger.error(
                f"Validation failed for '{item.get('slug', 'unknown')}' in table '{table}': {e}"
            )
            if validate:
                raise e
        raise RuntimeError(f"Failed to load item for table '{table}'.")


class DataLoader:
    def __init__(self, path: str, config: DatabaseConfig):
        self.path = path
        self.config = config

    def load_files(self, directory: TableName) -> dict[str, Any]:
        preloaded_data: dict[str, Any] = {}
        extensions = self.config.file_extensions
        for entry in os.scandir(os.path.join(self.path, directory)):
            if entry.is_file() and any(
                entry.name.endswith(ext) for ext in extensions
            ):
                try:
                    with open(entry.path) as fp:
                        if entry.name.endswith(".json"):
                            item = json.load(fp)
                        else:
                            item = yaml.safe_load(fp)
                    if isinstance(item, list):
                        for sub_item in item:
                            self._load_dict(
                                sub_item, entry.path, preloaded_data
                            )
                    else:
                        self._load_dict(item, entry.path, preloaded_data)
                except (
                    json.JSONDecodeError,
                    yaml.YAMLError,
                    FileNotFoundError,
                ) as e:
                    logger.error(f"Error loading file '{entry.path}': {e}")
        return preloaded_data

    def _load_dict(
        self,
        item: Mapping[str, Any],
        path: str,
        preloaded_data: dict[str, Any],
    ) -> None:
        if item["slug"] in preloaded_data:
            if path in preloaded_data[item["slug"]].get("paths", []):
                logger.error(
                    f"Error: Item with slug {item['slug']} was already loaded from this path ({path})."
                )
                return
            else:
                preloaded_data[item["slug"]]["paths"].append(path)
        else:
            preloaded_data[item["slug"]] = item
            preloaded_data[item["slug"]]["paths"] = [path]


class ModData:

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.preloaded: dict[TableName, dict[str, Any]] = {}
        self.database: dict[TableName, dict[str, DataModel]] = {}
        self.mod_metadata: dict[str, dict[str, Any]] = {}
        self.model_map = load_model_map(config.model_map)
        self.loader = ModelLoader(self.model_map)
        self._load_mod_metadata()
        self.path = ""
        if self.config.mod_tables:
            for mod, tables in self.config.mod_tables.items():
                if mod in self.config.active_mods:
                    for table in tables:
                        if table not in self.preloaded:
                            self.preloaded[table] = {}
                            self.database[table] = {}

    def _resolve_dependencies(self, mod: str) -> list[str]:
        resolver = DependencyResolver(self.config.mod_dependencies)
        return resolver.resolve(mod)

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
            if self.config.mod_tables:
                for mod, tables in self.config.mod_tables.items():
                    if mod in self.config.active_mods:
                        dependencies = self._resolve_dependencies(mod)
                        mods_to_load = dependencies + [mod]
                        for mod_to_load in mods_to_load:
                            if mod_to_load in self.config.mod_tables:
                                for table in self.config.mod_tables[
                                    mod_to_load
                                ]:
                                    self._preload_table(table, mod_to_load)
            else:
                logger.warning("No mod tables specified in config.")
        else:
            self._preload_table(directory, None)

    def _preload_table(
        self, table: TableName, mod_directory: Optional[str] = None
    ) -> None:
        active_mods = [
            mod
            for mod in self.config.active_mods
            if not self.config.mod_activation
            or self.config.mod_activation.get(mod, True)
        ]
        if mod_directory is None:
            for mod_directory in active_mods:
                self._preload_table_from_mod(table, mod_directory)
        else:
            self._preload_table_from_mod(table, mod_directory)

    def _preload_table_from_mod(
        self, table: TableName, mod_directory: str
    ) -> None:
        self.path = os.path.join(
            config.mod_base_path, mod_directory, config.mod_db_subfolder
        )
        if (
            self.config.mod_versions
            and mod_directory in self.config.mod_versions
        ):
            logger.info(
                f"Loading mod '{mod_directory}' version {self.config.mod_versions[mod_directory]}"
            )
        if not os.path.exists(self.path):
            logger.warning(f"Mod directory '{self.path}' not found.")
            return
        db_path = os.path.join(self.path, table)
        if (
            self.config.mod_table_exclusions
            and mod_directory in self.config.mod_table_exclusions
            and table in self.config.mod_table_exclusions[mod_directory]
        ):
            logger.info(f"Table '{table}' excluded by mod '{mod_directory}'.")
            return
        if os.path.exists(db_path):
            data_loader = DataLoader(self.path, self.config)
            if table not in self.preloaded:
                self.preloaded[table] = {}
            self.preloaded[table].update(data_loader.load_files(table))
        else:
            logger.warning(f"Database directory '{db_path}' not found.")

    def _load_mod_metadata(self) -> None:
        """Loads mod metadata from mod.json files."""
        loader = ModMetadataLoader(
            self.config.active_mods, config.mod_base_path
        )
        self.mod_metadata = loader.load_metadata()

    def load(
        self,
        directory: Union[TableName, Literal["all"]] = "all",
        validate: bool = True,
    ) -> None:
        """
        Loads all data from JSON files located under our data path.
        Parameters:
            directory: The directory under mods/tuxemon/db/ to load. Defaults
                to "all".
            validate: Whether or not we should raise an exception if validation
                fails
        """
        if directory == "all":
            if self.config.mod_tables:
                for mod, tables in self.config.mod_tables.items():
                    if mod in self.config.active_mods:
                        for table in tables:
                            self._load_models_from_preloaded(table, validate)
            else:
                logger.debug("No mod tables specified in config.")
        else:
            self._load_models_from_preloaded(directory, validate)

    def _load_models_from_preloaded(
        self, table: TableName, validate: bool
    ) -> None:
        """
        Loads models from the preloaded data into the main database.
        """
        for item in self.preloaded[table].values():
            if "paths" in item:
                del item["paths"]

            try:
                model = self.loader.load(item, table, validate)
                self.database[table][model.slug] = model
            except ValidationError as e:
                logger.error(
                    f"Failed to load model for item '{item.get('slug', 'unknown')}' in table '{table}': {e}"
                )

    def _validate_data(
        self, item: Mapping[str, Any], table: TableName
    ) -> DataModel:
        """Validates the given data."""
        try:
            model_class = self.model_map.get(table)
            if model_class:
                return model_class(**item)
            else:
                raise ValueError(f"Unexpected table: {table}")
        except ValidationError as e:
            logger.error(
                f"Validation failed for '{item['slug']}' in table '{table}': {e}"
            )
            raise e

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
        try:
            if validate:
                model = self._validate_data(item, table)
            else:
                model_class = self.model_map.get(table)
                if model_class:
                    model = model_class(**item)
                else:
                    raise ValueError(f"Unexpected table: {table}")

            self.database[table][model.slug] = model
        except ValidationError as e:
            logger.error(
                f"Validation failed for '{item['slug']}' in table '{table}': {e}"
            )
            if validate:
                raise e

    @overload
    def lookup(self, slug: str) -> MonsterModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["monster"]) -> MonsterModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["status"]) -> StatusModel:
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
    def lookup(self, slug: str, table: Literal["taste"]) -> TasteModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["shape"]) -> ShapeModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["terrain"]) -> TerrainModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["weather"]) -> WeatherModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["template"]) -> TemplateModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["mission"]) -> MissionModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["music"]) -> MusicModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["animation"]) -> AnimationModel:
        pass

    @overload
    def lookup(self, slug: str, table: Literal["sounds"]) -> SoundModel:
        pass

    @overload
    def lookup(
        self, slug: str, table: Literal["environment"]
    ) -> EnvironmentModel:
        pass

    def lookup(
        self, slug: str, table: Optional[TableName] = None
    ) -> DataModel:
        """
        Looks up a monster, technique, item, npc, etc based on slug.

        Parameters:
            slug: The slug of the monster, technique, item, or npc.  A short
                English identifier.
            table: Which index to do the search in.

        Returns:
            A pydantic.BaseModel from the resulting lookup.
        """
        if table is None:
            table = self.config.default_lookup_table
        table_entry = self.database.get(table)
        if not table_entry:
            raise ValueError(f"{table} table wasn't loaded")
        if slug not in table_entry:
            self.log_missing_entry_and_raise(table, slug)
        return table_entry[slug]

    def log_missing_entry_and_raise(self, table: TableName, slug: str) -> None:
        """Logs a missing entry and raises EntryNotFoundError."""
        options = difflib.get_close_matches(slug, self.database[table].keys())
        options_str = ", ".join(repr(s) for s in options)
        hint = (
            f"Did you mean {options_str}?"
            if options
            else "No similar slugs found."
        )
        raise EntryNotFoundError(
            f"Lookup failed for unknown {table} '{slug}'. {hint}"
        )

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
        entry = self.database[table].get(slug)
        if entry:
            file_name = getattr(entry, "file", None)
            if file_name:
                return str(file_name)
            else:
                return slug
        else:
            raise EntryNotFoundError(
                f"Entry {slug} not found in table '{table}'."
            )

    def has_entry(self, slug: str, table: TableName) -> bool:
        table_entry = self.database[table]
        if not table_entry:
            raise ValueError(f"{table} table wasn't loaded")
        return slug in table_entry

    def reload(self, table: TableName, validate: bool = True) -> None:
        """Reloads the data for a specific table."""
        if table not in self.database:
            logger.error(f"Table '{table}' not loaded.")
            return

        if table in self.preloaded:
            logger.info(f"Clearing preloaded data for table '{table}'.")
            self.preloaded[table] = {}
        if table in self.database:
            logger.info(f"Resetting database entries for table '{table}'.")
            self.database[table] = {}

        try:
            if table in self.config.mod_tables:
                mods_associated = [
                    mod
                    for mod, tables in self.config.mod_tables.items()
                    if table in tables and mod in self.config.active_mods
                ]
                for mod in mods_associated:
                    mod_path = os.path.join(
                        self.config.mod_base_path,
                        mod,
                        self.config.mod_db_subfolder,
                    )
                    logger.info(
                        f"Preloading table '{table}' from mod path '{mod_path}'."
                    )
                    self._preload_table_from_mod(table, mod)

            self._load_models_from_preloaded(table, validate)
        except Exception as e:
            logger.error(f"Error reloading table '{table}': {e}")

    def add_entry(
        self, table: TableName, data: dict[str, Any], validate: bool = True
    ) -> None:
        try:
            model = self.loader.load(data, table, validate)

            if table not in self.database:
                self.database[table] = {}

            if model.slug in self.database[table]:
                logger.error(
                    f"Entry with slug '{model.slug}' already exists in table '{table}'. Skipping addition."
                )
                return

            self.database[table][model.slug] = model
            logger.info(
                f"Entry '{model.slug}' added to table '{table}' successfully!"
            )

        except ValidationError as e:
            logger.error(
                f"Validation failed for entry '{data.get('slug', 'unknown')}' in table '{table}': {e}"
            )
            if validate:
                raise e
        except Exception as ex:
            logger.error(
                f"Unexpected error while adding entry to table '{table}': {ex}"
            )


def load_config(config_path: str) -> DatabaseConfig:
    """Loads configuration from a JSON file."""
    try:
        with open(config_path) as f:
            data = json.load(f)
        return DatabaseConfig(**data)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Configuration file '{config_path}' not found."
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in '{config_path}': {e}")


class Validator:
    """
    Helper class for validating resources exist.
    """

    def __init__(self, database: ModData) -> None:
        self.db = database
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
        with Image.open(path) as sprite:
            native = prepare.NATIVE_RESOLUTION
            if size == native:
                if not (
                    sprite.size[0] <= size[0] and sprite.size[1] <= size[1]
                ):
                    raise ValueError(
                        f"{file} has size {sprite.size}, but must be less than or equal to {native}"
                    )
            else:
                if sprite.size != size:
                    raise ValueError(
                        f"{file} has size {sprite.size}, but must be {size}"
                    )
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
        return slug in self.db.preloaded[table]


path = prepare.fetch(mods_folder, "db_config.json")
config = load_config(path)
# Global database container
db = ModData(config)
# Validator container
has = Validator(db)
