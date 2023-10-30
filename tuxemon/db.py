# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import difflib
import json
import logging
import os
import sys
from enum import Enum
from operator import itemgetter
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Union,
    overload,
)

from pydantic import (
    BaseModel,
    Field,
    FieldValidationInfo,
    ValidationError,
    field_validator,
)
from typing_extensions import Annotated

from tuxemon import prepare
from tuxemon.locale import T

logger = logging.getLogger(__name__)

# Load the default translator for data validation
T.collect_languages(False)
T.load_translator()

# Target is a mapping of who this targets
Target = Mapping[str, int]


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


class ItemType(str, Enum):
    consumable = "Consumable"
    key_item = "KeyItem"


class ItemCategory(str, Enum):
    none = "none"
    badge = "badge"
    booster = "booster"
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
    ran = "ran"
    forfeit = "forfeit"


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


class EvolutionType(str, Enum):
    element = "element"
    gender = "gender"
    item = "item"
    location = "location"
    season = "season"
    daytime = "daytime"
    standard = "standard"
    stat = "stat"
    tech = "tech"


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


# TODO: Automatically generate state enum through discovery
State = Enum(
    "State",
    {
        "MainCombatMenuState": "MainCombatMenuState",
        "WorldState": "WorldState",
        "None": "",
    },
)


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
    type: ItemType = Field(..., description="The type of item this is")
    category: ItemCategory = Field(
        ..., description="The category of item this is"
    )
    usable_in: Sequence[State] = Field(
        ..., description="State(s) where this item can be used."
    )
    # TODO: We'll need some more advanced validation logic here to parse item
    # conditions and effects to ensure they are formatted properly.
    conditions: Sequence[str] = Field(
        [], description="Conditions that must be met"
    )
    effects: Sequence[str] = Field(
        [], description="Effects this item will have"
    )

    class Config:
        title = "Item"

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
        if has.file(v):
            return v
        raise ValueError(f"the sprite {v} doesn't exist in the db")


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
        ..., description="Monster level in which this moveset is learned"
    )
    technique: str = Field(
        ..., description="Name of the technique for this moveset item"
    )
    element: Optional[ElementType] = Field(
        None, description="Element random technique"
    )

    @field_validator("level_learned")
    def valid_level(cls: MonsterMovesetItemModel, v: int) -> int:
        if v < 0:
            raise ValueError(f"invalid level learned: {v}")
        return v

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
    path: EvolutionType = Field(..., description="Paths to evolution")
    at_level: int = Field(
        ...,
        description="The level at which this item can be used for evolution",
    )
    monster_slug: str = Field(
        ..., description="The monster slug that this evolution item applies to"
    )
    # optional fields
    element: Optional[ElementType] = Field(
        None, description="Element parameter"
    )
    gender: Optional[GenderType] = Field(None, description="Gender parameter")
    item: Optional[str] = Field(None, description="Item parameter.")
    inside: bool = Field(
        None,
        description="Location parameter: inside true or inside false (outside).",
    )
    season: Optional[str] = Field(None, description="Season parameter.")
    daytime: Optional[str] = Field(None, description="Daytime parameter.")
    stat1: Optional[StatType] = Field(
        None, description="Stat parameter stat1 >= stat2."
    )
    stat2: Optional[StatType] = Field(
        None, description="Stat parameter stat2 < stat1."
    )
    tech: Optional[str] = Field(None, description="Technique parameter.")

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

    @field_validator("item")
    def item_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")


class MonsterFlairItemModel(BaseModel):
    category: str = Field(..., description="The category of this flair item")
    names: Sequence[str] = Field(..., description="The names")


class MonsterSpritesModel(BaseModel):
    battle1: str = Field(..., description="The battle1 sprite")
    battle2: str = Field(..., description="The battle2 sprite")
    menu1: str = Field(..., description="The menu1 sprite")
    menu2: str = Field(..., description="The menu2 sprite")

    # Validate resources that should exist
    @field_validator("battle1", "battle2", "menu1", "menu2")
    def file_exists(cls: MonsterSpritesModel, v: str) -> str:
        if has.file(f"{v}.png"):
            return v
        raise ValueError(f"no resource exists with path: {v}")


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
    txmn_id: int = Field(..., description="The id of the monster")
    height: float = Field(..., description="The height of the monster")
    weight: float = Field(..., description="The weight of the monster")
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
    types: Sequence[ElementType] = Field(
        [], description="The type(s) of this monster"
    )
    catch_rate: float = Field(0, description="The catch rate of the monster")
    possible_genders: Sequence[GenderType] = Field(
        [], description="Valid genders for the monster"
    )
    lower_catch_resistance: float = Field(
        0, description="The lower catch resistance of the monster"
    )
    upper_catch_resistance: float = Field(
        0, description="The upper catch resistance of the monster"
    )
    moveset: Sequence[MonsterMovesetItemModel] = Field(
        [], description="The moveset of this monster"
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

    class Config:
        # Validate assignment allows us to assign a default inside a validator
        validate_assignment = True

    # Set the default sprites based on slug. Specifying 'always' is needed
    # because by default pydantic doesn't validate null fields.
    @field_validator("sprites")
    def set_default_sprites(
        cls: MonsterModel, v: str, info: FieldValidationInfo
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
    value: float = Field(0.0, description="The value of the stat")
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


# TechSort defines the sort of technique a technique is.
class TechSort(str, Enum):
    damage = "damage"
    meta = "meta"


class CategoryCondition(str, Enum):
    negative = "negative"
    positive = "positive"


class ResponseCondition(str, Enum):
    replaced = "replaced"
    removed = "removed"


class TechniqueModel(BaseModel):
    slug: str = Field(..., description="The slug of the technique")
    sort: TechSort = Field(..., description="The sort of technique this is")
    icon: str = Field(None, description="The icon to use for the technique")
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
    power: float = Field(0, description="Power of the technique")
    is_fast: bool = Field(
        False, description="Whether or not this is a fast technique"
    )
    randomly: bool = Field(
        True,
        description="Whether or not this technique will be picked by random",
    )
    healing_power: int = Field(0, description="Value of healing power.")
    recharge: int = Field(0, description="Recharge of this technique")
    range: Range = Field(..., description="The attack range of this technique")
    tech_id: int = Field(..., description="The id of this technique")
    accuracy: float = Field(0, description="The accuracy of the technique")
    potency: Optional[float] = Field(
        None, description="How potent the technique is"
    )

    # Validate resources that should exist
    @field_validator("icon")
    def file_exists(cls: TechniqueModel, v: str) -> str:
        if has.file(v):
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
        cls: TechniqueModel, v: Range, info: FieldValidationInfo
    ) -> Range:
        # Special indicates that we are not doing damage
        if v == Range.special and "damage" in info.data["effects"]:
            raise ValueError(
                '"special" range cannot be used with effect "damage"'
            )

        return v

    @field_validator("animation")
    def animation_exists(
        cls: TechniqueModel, v: Optional[str]
    ) -> Optional[str]:
        file: str = f"animations/technique/{v}_00.png"
        if not v or has.file(file):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")


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
    target: Target = Field(
        ..., description="Target mapping of who this condition is used on"
    )
    animation: Optional[str] = Field(
        None, description="Animation to play for this condition"
    )
    sfx: str = Field(
        ..., description="Sound effect to play when this condition is used"
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
        description="With which status reply after a tech used",
    )
    repl_item: Optional[str] = Field(
        None,
        description="With which status reply after an item used",
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
        if has.file(v):
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
        if not v or has.file(file):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")

    @field_validator("repl_tech", "repl_item")
    def status_exists(cls: ConditionModel, v: Optional[str]) -> Optional[str]:
        if not v or has.db_entry("condition", v):
            return v
        raise ValueError(f"the status {v} doesn't exist in the db")


class PartyMemberModel(BaseModel):
    slug: str = Field(..., description="Slug of the monster")
    level: int = Field(..., description="Level of the monster")
    money_mod: int = Field(
        ..., description="Modifier for money this monster gives"
    )
    exp_req_mod: int = Field(..., description="Experience required modifier")
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
        sprite: str = f"sprites/{v}_front.png"
        sprite_obj: str = f"sprites_obj/{v}.png"
        if has.file(sprite) or has.file(sprite_obj):
            return v
        raise ValueError(f"the sprite {v} doesn't exist in the db")

    @field_validator("slug")
    def template_exists(cls: NpcTemplateModel, v: str) -> str:
        if has.db_entry("template", v):
            return v
        raise ValueError(f"the template {v} doesn't exist in the db")


class NpcModel(BaseModel):
    slug: str = Field(..., description="Slug of the name of the NPC")
    forfeit: bool = Field(True, description="Whether you can forfeit or not")
    template: Sequence[NpcTemplateModel] = Field(
        [], description="List of templates"
    )
    monsters: Sequence[PartyMemberModel] = Field(
        [], description="List of monsters in the NPCs party"
    )
    items: Sequence[BagItemModel] = Field(
        [], description="List of items in the NPCs bag"
    )


class BattleGraphicsModel(BaseModel):
    island_back: str = Field(..., description="Sprite used for back combat")
    island_front: str = Field(..., description="Sprite used for front combat")
    background: str = Field(..., description="Sprite used for background")

    # Validate resources that should exist
    @field_validator("island_back", "island_front", "background")
    def file_exists(cls: BattleGraphicsModel, v: str) -> str:
        file: str = f"gfx/ui/combat/{v}"
        if has.file(file):
            return v
        raise ValueError(f"no resource exists with path: {file}")


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
    daytime: bool = Field(
        True, description="Options: day (true), night (false)"
    )
    exp_req_mod: int = Field(1, description="Exp modifier wild monster")

    @field_validator("monster")
    def monster_exists(cls: EncounterItemModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class EncounterModel(BaseModel):
    slug: str = Field(
        ..., description="Slug to uniquely identify this encounter"
    )
    monsters: Sequence[EncounterItemModel] = Field(
        [], description="Monsters encounterable"
    )


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
        if has.file(v):
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


class EconomyModel(BaseModel):
    slug: str = Field(..., description="Slug uniquely identifying the economy")
    items: Sequence[EconomyItemModel]


class TemplateModel(BaseModel):
    slug: str = Field(
        ..., description="Slug uniquely identifying the template"
    )
    double: bool = Field(False, description="Whether triggers 2vs2 or not")


class MusicModel(BaseModel):
    slug: str = Field(..., description="Unique slug for the music")
    file: str = Field(..., description="File for the music")


class SoundModel(BaseModel):
    slug: str = Field(..., description="Unique slug for the sound")
    file: str = Field(..., description="File for the sound")


TableName = Literal[
    "economy",
    "element",
    "shape",
    "template",
    "encounter",
    "environment",
    "item",
    "monster",
    "music",
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
    EncounterModel,
    EnvironmentModel,
    ItemModel,
    MonsterModel,
    MusicModel,
    NpcModel,
    SoundModel,
    ConditionModel,
    TechniqueModel,
]


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
        self._tables: List[TableName] = [
            "item",
            "monster",
            "npc",
            "condition",
            "technique",
            "encounter",
            "environment",
            "sounds",
            "music",
            "economy",
            "element",
            "shape",
            "template",
        ]
        self.preloaded: Dict[TableName, Dict[str, Any]] = {}
        self.database: Dict[TableName, Dict[str, Any]] = {}
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
        self.path = prepare.fetch("db")
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

    def load_json(self, directory: TableName, validate: bool = False) -> None:
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
                    self.load_dict(sub, directory)
            else:
                self.load_dict(item, directory)

    def load_dict(self, item: Mapping[str, Any], table: TableName) -> None:
        """
        Loads a single json object and adds it to the appropriate preload db
        table.

        Parameters:
            item: The json object to load in.
            table: The db table to load the object into.

        """
        if item["slug"] in self.preloaded[table]:
            logger.warning(
                "Error: Item with slug %s was already loaded.",
                item,
            )
            return
        self.preloaded[table][item["slug"]] = item

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
            elif table == "encounter":
                encounter = EncounterModel(**item)
                self.database[table][encounter.slug] = encounter
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
            "encounter",
            "environment",
            "item",
            "monster",
            "music",
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
