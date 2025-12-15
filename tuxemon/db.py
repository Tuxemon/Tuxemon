# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from importlib import import_module
from math import isclose
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from tuxemon import prepare
from tuxemon.constants.asset_loader import (
    fetch_asset,
    fetch_mod_asset_roots,
)
from tuxemon.constants.paths import mods_folder
from tuxemon.database.config import EntryNotFoundError
from tuxemon.database.data import ModData
from tuxemon.database.loader import ModelLoader
from tuxemon.database.utils import load_config
from tuxemon.database.validator import Validator
from tuxemon.formula import config_monster
from tuxemon.locale import T
from tuxemon.surfanim import FlipAxes

logger = logging.getLogger(__name__)

# Load the default translator for data validation
T.initialize_translations()


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
    carrier = "carrier"
    recovered = "recovered"


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


class ItemRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


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
    food = "food"
    doll = "doll"


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


class Temperature(str, Enum):
    freezing = "freezing"
    cold = "cold"
    mild = "mild"
    warm = "warm"
    hot = "hot"
    scorching = "scorching"


class Wind(str, Enum):
    calm = "calm"
    breezy = "breezy"
    windy = "windy"
    gusty = "gusty"
    stormy = "stormy"


class EffectPhase(Enum):
    CHECK_PARTY_HP = "check_party_hp"
    DEFAULT = "default"
    ENQUEUE_ITEM = "enqueue_item"
    ON_END = "on_end"
    ON_FAINT = "on_faint"
    ON_START = "on_start"
    ON_DECISION = "on_decision"
    PERFORM_ITEM = "perform_item"
    PERFORM_STATUS = "perform_status"
    PERFORM_TECH = "perform_tech"
    PRE_CHECKING = "pre_checking"
    SWAP_MONSTER = "swap_monster"
    ON_STEP_INTERVAL = "on_step_interval"


class Acquisition(str, Enum):
    UNKNOWN = "unknown"
    CAPTURED = "captured"
    TRADED = "traded"
    BRED = "bred"
    GIFTED = "gifted"
    PURCHASED = "purchased"
    RESCUED = "rescued"
    CREATED = "created"


class ExperienceMethod(Enum):
    DEFAULT = "default"
    XP_EQUAL = "xp_equal"
    XP_TRANSMITTER = "xp_transmitter"
    XP_FEEDER = "xp_feeder"
    XP_OVERKILL = "xp_overkill"
    XP_DAMAGE_PROP = "xp_damage_prop"
    XP_BOND = "xp_bond"
    XP_STAGE = "xp_stage"
    XP_SURVIVOR = "xp_survivor"


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

U = TypeVar("U", bound="BaseLookupModel")


class BaseLookupModel(ABC):
    table_name: ClassVar[str]

    @classmethod
    @abstractmethod
    def lookup(cls: type[U], slug: str, db: ModData) -> U:
        pass


class ColorModel(BaseModel):
    red: int = Field(..., ge=0, le=255)
    green: int = Field(..., ge=0, le=255)
    blue: int = Field(..., ge=0, le=255)
    alpha: int = Field(255, ge=0, le=255)


class BoundingBox(BaseModel):
    x: int = Field(
        ...,
        description="The X-coordinate of the top-left corner of the bounding box.",
    )
    y: int = Field(
        ...,
        description="The Y-coordinate of the top-left corner of the bounding box.",
    )
    width: int = Field(
        ...,
        description="The horizontal size of the bounding box. Must be a positive integer.",
        gt=0,
    )
    height: int = Field(
        ...,
        description="The vertical size of the bounding box. Must be a positive integer.",
        gt=0,
    )


class Operator(str, Enum):
    IS = "is"
    NOT = "not"


class ParameterizableRule(BaseModel):
    """
    Base model for any component (condition or action) that requires type,
    parameters, and an optional name.
    """

    type: str = Field(
        ..., description="The functional type or command of the rule."
    )
    parameters: Sequence[str] = Field(
        default_factory=list,
        description="A list of string arguments for the rule type.",
    )
    name: str = Field(
        "unnamed_rule",
        description="User-defined name or identifier for the rule.",
    )


class LogicCondition(ParameterizableRule):
    """The generic, non-spatial condition model with operator validation."""

    operator: Operator = Field(
        ..., description="Logical operator: 'is' or 'not'"
    )


class SpatialCondition(LogicCondition):
    """Represents a condition that inherits generic logic and adds a spatial component."""

    box: BoundingBox = Field(
        ..., description="The spatial bounding box for this condition."
    )


class EventObject(BaseModel):
    """The main container entity for a game/map event."""

    id: int = Field(
        ...,
        description="The unique, optional database ID of the event object.",
    )
    name: str = Field(
        ..., description="The displayed, human-readable name of the event."
    )
    priority: int = Field(
        ...,
        description="Order of evaluation relative to other EventObjects. Higher number (e.g., 10) is higher priority.",
        ge=0,
    )
    timeout: Optional[float] = Field(
        None,
        description="Maximum duration (in seconds) this event is allowed to run. None = no timeout.",
    )
    delay: Optional[float] = Field(
        None,
        description="Delay before the event starts processing (in seconds). None = no delay.",
    )
    box: BoundingBox = Field(
        ..., description="The spatial bounding box of the event."
    )
    conds: Sequence[SpatialCondition] = Field(
        default_factory=list,
        description="A sequence of conditions (spatial or logic) that must all be met to trigger the actions.",
    )
    acts: Sequence[ParameterizableRule] = Field(
        default_factory=list,
        description="A sequence of actions/effects to execute when conditions are met.",
    )


class BaseComparison(BaseModel):
    comparison: Comparison = Field(
        ...,
        description="The type of comparison to perform (e.g., greater_than, equal_to).",
    )
    target_value: Optional[int] = Field(
        None,
        description="An optional fixed numeric value to compare against (e.g., stat must be greater than 50).",
    )


class StatsComparison(BaseComparison):
    stat_type: StatType = Field(
        ...,
        description="The primary stat being evaluated for the evolution condition (e.g., speed, defense).",
    )
    target_stat: Optional[StatType] = Field(
        None,
        description="An optional secondary stat to compare against the primary stat (e.g., compare speed to defense).",
    )


class BondComparison(BaseComparison):
    value: int = Field(
        ...,
        description="The bond value to compare against.",
        ge=config_monster.bond_range[0],
        le=config_monster.bond_range[1],
    )


class PartyConditionsModel(BaseModel):
    monster_slugs: Optional[dict[str, int]] = Field(
        None,
        description="A dictionary specifying required monsters and their minimum counts by slug.",
    )
    monster_types: Optional[dict[str, int]] = Field(
        None,
        description="A dictionary specifying required monster types and their minimum counts.",
    )
    genders: Optional[dict[GenderType, int]] = Field(
        None,
        description="A dictionary specifying required genders and their minimum counts.",
    )
    alignment: Optional[str] = Field(
        None,
        description="The elemental alignment the party must lean toward for evolution to occur.",
    )

    @field_validator("monster_slugs")
    def validate_monster_slugs(
        cls, v: Optional[dict[str, int]]
    ) -> Optional[dict[str, int]]:
        if v:
            for slug, count in v.items():
                if not has.db_entry("monster", slug):
                    raise ValueError(
                        f"Monster slug '{slug}' does not exist in the database."
                    )
                if not (0 <= count < prepare.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for monster slug '{slug}' must be between 0 and {prepare.PARTY_LIMIT - 1}."
                    )
        return v

    @field_validator("monster_types")
    def validate_monster_types(
        cls, v: Optional[dict[str, int]]
    ) -> Optional[dict[str, int]]:
        if v:
            for type_, count in v.items():
                if not (0 <= count < prepare.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for monster type '{type_}' must be between 0 and {prepare.PARTY_LIMIT - 1}."
                    )
        return v

    @field_validator("genders")
    def validate_genders(
        cls, v: Optional[dict[GenderType, int]]
    ) -> Optional[dict[GenderType, int]]:
        if v:
            for gender, count in v.items():
                if not (0 <= count < prepare.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for gender '{gender}' must be between 0 and {prepare.PARTY_LIMIT - 1}."
                    )
        return v


class Behaviors(BaseModel):
    """Base class for shared behaviors."""

    requires_monster_menu: bool = Field(
        True, description="Whether a monster menu is required for this action."
    )
    show_dialog_on_success: bool = Field(
        True, description="Whether to show a dialogue after a successful use."
    )
    show_dialog_on_failure: bool = Field(
        True, description="Whether to show a dialogue after a failed use."
    )


class MenuAction(BaseModel):
    key: str = Field(..., description="Internal action slug/key.")
    display_text: str = Field(
        ..., description="Translation key for the menu label."
    )

    @field_validator("display_text")
    def translation_exists(cls: MenuAction, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class ItemBehaviors(Behaviors):
    """Behaviors specific to items."""

    consumable: bool = Field(
        True, description="Whether or not this item is consumable."
    )
    visible: bool = Field(
        True, description="Whether this is visible in the UI."
    )
    resellable: bool = Field(False, description="Whether this can be resold.")
    throwable: bool = Field(
        False, description="Whether or not this item is throwable."
    )
    holdable: bool = Field(
        False, description="Whether or not this item is holdable."
    )
    repairable: bool = Field(
        False, description="Whether this can be repaired."
    )
    craftable: bool = Field(False, description="Whether this can be crafted.")


class TechBehaviors(Behaviors):
    """Behaviors specific to techniques."""

    is_field_tech: bool = Field(
        False,
        description="Whether this technique can be used in the overworld.",
    )
    bypasses_selection: bool = Field(
        False,
        description="Whether this technique skips target selection and applies directly to the user’s monster.",
    )


class StatusBehaviors(Behaviors):
    """Behaviors specific to statuses."""

    persists_after_combat: bool = Field(
        False,
        description="Whether this status effect remains active after combat ends.",
    )


class SoundProperties(BaseModel):
    sfx: Optional[str] = Field(..., description="Sound effect to play")
    volume: float = Field(..., ge=0.0, description="Playback volume")

    @field_validator("sfx")
    def sfx_exists(cls: SoundProperties, v: Optional[str]) -> Optional[str]:
        if not v:
            return v

        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class MusicProperties(BaseModel):
    music: Optional[str] = Field(..., description="Music to play")
    volume: float = Field(..., ge=0.0, description="Playback volume")

    @field_validator("music")
    def music_exists(cls: MusicProperties, v: Optional[str]) -> Optional[str]:
        if not v:
            return v

        if has.db_entry("music", v):
            return v
        raise ValueError(f"the music {v} doesn't exist in the db")


class VisualProperties(BaseModel):
    animation: Optional[str] = Field(
        ..., description="The slug or path of the animation to play."
    )
    flip_axes: FlipAxes = Field(
        ...,
        description="Axes (X and/or Y) along which the visual should be flipped.",
    )
    loop: int = Field(
        ...,
        description=(
            "Number of times the visual should loop. "
            "-1 means infinite looping, 0 means play once, "
            "any positive integer means loop that many times."
        ),
    )

    @field_validator("animation")
    def animation_exists(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v

        item_file = f"animations/item/{v}_00.png"
        technique_file = f"animations/technique/{v}_00.png"

        if has.db_entry("animation", v) and (
            has.size(item_file, prepare.NATIVE_RESOLUTION)
            or has.size(technique_file, prepare.NATIVE_RESOLUTION)
        ):
            return v

        raise ValueError(
            f"the animation {v} doesn't exist in item/ or technique/ db"
        )


class DynamicMenuEntry(BaseModel):
    position: int
    label_key: str
    state: str
    menu_type: str
    enabled: bool = True


class ItemModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "item"
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
    confirm_text: str = Field(
        "item_confirm_use",
        description="Translation key for the label used when confirming item usage.",
    )
    cancel_text: str = Field(
        "item_confirm_cancel",
        description="Translation key for the label used when canceling item usage.",
    )
    menu_actions: Sequence[MenuAction] = Field(
        default_factory=list,
        description="Custom list of menu actions (key, display_text) for this item.",
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
    conditions: Sequence[LogicCondition] = Field(
        default_factory=list, description="Conditions that must be met"
    )
    effects: Sequence[ParameterizableRule] = Field(
        ..., description="Effects this item will have"
    )
    visuals: VisualProperties = Field(
        ..., description="Configuration for the item's visual display."
    )
    sound: SoundProperties = Field(
        ..., description="Configuration for the item's sound playback."
    )
    dynamic_menu: Optional[DynamicMenuEntry] = Field(
        None,
        description="Item adds a button to a specific menu (world, phone, etc.).",
    )
    rarity: ItemRarity = Field(
        ItemRarity.COMMON,
        description="The rarity tier for display and loot logic.",
    )
    cost: int = Field(0, description="The standard cost of the item.", ge=0)
    reward_method: ExperienceMethod = Field(
        ExperienceMethod.DEFAULT,
        description="Method applied by a held item to calculate experience gained as a battle reward.",
    )
    money_multiplier: float = Field(
        1.0,
        description="Multiplier applied by a held item to calculate money gained as a battle reward.",
        ge=0,
    )
    max_wear: int = Field(
        0,
        description="The maximum wear threshold before the item breaks or becomes unusable.",
        ge=0,
    )
    break_chance: float = Field(
        0.0,
        description="Chance (0.0-1.0) that the item breaks each time it's used.",
        ge=0.0,
        le=1.0,
    )
    modifiers: list[Modifier] = Field(..., description="Various modifiers")
    immunity_to_status: Sequence[str] = Field(
        default_factory=list,
        description="Statuses this item grants immunity to",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> ItemModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(ItemModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Item {slug} not found")

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

    @field_validator("immunity_to_status")
    def status_exists(cls: ItemModel, v: Sequence[str]) -> Sequence[str]:
        if v:
            for status in v:
                if status != "all" and not has.db_entry("status", status):
                    raise ValueError(
                        f"A status {status} doesn't exist in the db"
                    )
        return v


class AttributesModel(BaseModel):
    armour: int = Field(..., description="Armour value")
    dodge: int = Field(..., description="Dodge value")
    hp: int = Field(..., description="HP (Hit Points) value")
    melee: int = Field(..., description="Melee value")
    ranged: int = Field(..., description="Ranged value")
    speed: int = Field(..., description="Speed value")


class ShapeModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "shape"
    slug: str = Field(
        ..., description="Slug of the shape, used as a unique identifier."
    )
    attributes: AttributesModel = Field(
        ..., description="Statistical attributes of the shape."
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> ShapeModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(ShapeModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Shape {slug} not found")

    @field_validator("slug")
    def translation_exists_shape(cls: ShapeModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class LearningMethod(str, Enum):
    LEVEL_UP = "level_up"
    TM = "tm"
    EVENT = "event"
    EVOLUTION = "evolution"


class MonsterMovesetItemModel(BaseModel):
    level_learned: int = Field(
        ..., description="Monster level in which this moveset is learned", gt=0
    )
    technique: str = Field(
        ...,
        description="Name of the technique for this moveset item",
    )
    evolution_stage_learned: Optional[EvolutionStage] = Field(
        None,
        description="Evolution stage at which this technique is learned. If None, not tied to a specific evolution stage beyond level.",
    )
    can_be_forgotten: bool = Field(
        True,
        description="Indicates if this technique can be forgotten by the monster.",
    )
    learning_method: LearningMethod = Field(
        LearningMethod.LEVEL_UP,
        description="Method by which the technique is learned.",
    )

    @field_validator("technique")
    def technique_exists(cls: MonsterMovesetItemModel, v: str) -> str:
        if has.db_entry("technique", v):
            return v
        raise ValueError(f"the technique {v} doesn't exist in the db")


class MonsterHistoryItemModel(BaseModel):
    slug: str = Field(
        ..., description="The monster slug in the evolution path."
    )
    stage: EvolutionStage = Field(
        ..., description="The evolution stage of the monster."
    )
    evolves_from: list[str] = Field(
        default_factory=list, description="Monsters this monster evolves from."
    )
    evolves_into: list[str] = Field(
        default_factory=list,
        description="Monsters this monster can evolve into.",
    )

    @field_validator("slug", "evolves_from", "evolves_into")
    def validate_monsters_exist(
        cls, v: Union[str, list[str]]
    ) -> Union[str, list[str]]:
        if isinstance(v, str):
            if has.db_entry("monster", v):
                return v
            raise ValueError(f"Monster slug '{v}' not found in database.")
        elif isinstance(v, list):
            for slug in v:
                if not has.db_entry("monster", slug):
                    raise ValueError(
                        f"Monster slug '{slug}' not found in database."
                    )
            return v
        return v


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
    item: Optional[dict[str, float]] = Field(
        None,
        description=(
            "A dictionary of item slugs and their associated evolution weights. "
            "Weights are relative and will be normalized to sum to 1.0. "
            "Each item must exist in the database and have a non-negative weight."
        ),
    )
    inside: Optional[bool] = Field(
        None,
        description="Whether the monster must be inside to evolve.",
    )
    acquisition: Optional[Acquisition] = Field(
        None,
        description="How the monster was obtained (e.g. caught, bred, traded, gifted).",
    )
    variables: Sequence[dict[str, str]] = Field(
        default_factory=list,
        description="The game variables that must exist and match a specific value for the monster to evolve.",
        min_length=1,
    )
    stats: Optional[StatsComparison] = Field(
        None,
        description=(
            "Defines a condition where one monster stat must compare to another stat or value "
            "for evolution to occur. For example, 'speed must be greater than defense'. "
            "Includes the stat being evaluated, the type of comparison (e.g., greater_than, equal_to), "
            "and the target stat or value."
        ),
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
        default_factory=list,
        description="The techniques that the monster must have learned for the evolution to occur.",
        min_length=1,
        max_length=prepare.MAX_MOVES,
    )
    bond: Optional[BondComparison] = Field(
        None,
        description=(
            "Defines a condition where the monster's bond must meet a specific comparison to evolve. "
            "Includes the comparison type (e.g., greater_than, equals) and the target bond value. "
            "For example, 'bond must be greater than 50'."
        ),
    )
    tastes: Optional[dict[str, str]] = Field(
        None,
        description="A dictionary of taste values required for the monster to evolve (e.g., {'cold': 'value', 'warm': 'value'}).",
    )
    probability: Optional[float] = Field(
        None,
        description="Chance (0.0 to 1.0) that this evolution occurs when conditions are met.",
    )
    held_item: Optional[str] = Field(
        None, description="Item slug the monster must be holding to evolve."
    )
    party_conditions: Optional[PartyConditionsModel] = Field(
        None,
        description="Complex conditions based on the player's party required for evolution.",
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

    @field_validator("tastes")
    def validate_tastes(
        cls, v: Optional[dict[str, str]]
    ) -> Optional[dict[str, str]]:
        if v:  # Only proceed if the tastes dictionary is not None
            for taste_value in v.values():
                if not has.db_entry("taste", taste_value):
                    raise ValueError(
                        f"The taste '{taste_value}' does not exist in the database."
                    )
        return v

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

    @field_validator("item")
    def validate_item_and_weights(
        cls: MonsterEvolutionItemModel, v: Optional[dict[str, float]]
    ) -> Optional[dict[str, float]]:
        if v is None:
            return v

        total_weight = 0.0
        for item_slug, weight in v.items():
            if not has.db_entry("item", item_slug):
                raise ValueError(
                    f"The item '{item_slug}' doesn't exist in the database."
                )
            if weight < 0.0:
                raise ValueError(
                    f"Weight for item '{item_slug}' must be non-negative."
                )
            total_weight += weight

        if total_weight == 0.0:
            raise ValueError(
                "Total weight must be greater than 0.0 to normalize."
            )

        normalized = {
            slug: weight / total_weight for slug, weight in v.items()
        }
        return normalized

    @field_validator("held_item")
    def held_item_exists(
        cls: MonsterEvolutionItemModel, v: Optional[str]
    ) -> Optional[str]:
        if not v or has.db_entry("item", v):
            return v
        raise ValueError(f"the held item {v} doesn't exist in the db")


class FlairModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "flair"

    slug: str = Field(..., description="The unique name of the flair.")
    category: str = Field(..., description="The category of this flair item.")
    weight: float = Field(
        1.0,
        description="A value representing the flair's rarity or probability.",
        ge=0,
    )
    layer: int = Field(
        0,
        description="The drawing layer for the flair. Higher numbers are drawn on top.",
    )
    layer_order: int = Field(
        0,
        description="The drawing order for flairs within the same layer. Lower numbers are drawn first.",
    )
    x_offset: Optional[int] = Field(
        None,
        description="The horizontal offset of the flair from the sprite's origin.",
    )
    y_offset: Optional[int] = Field(
        None,
        description="The vertical offset of the flair from the sprite's origin.",
    )
    sprite_type: Optional[set[str]] = Field(
        None,
        description="Specifies which sprite type this flair applies to (e.g., 'front', 'back', 'menu01'). If None, applies to all.",
    )
    sprite_type_override: Optional[str] = Field(
        None,
        description="Overrides the default sprite type used in the file path (e.g., 'universal').",
    )
    color: Optional[ColorModel] = Field(
        None, description="The color tint to apply to the flair sprite."
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> FlairModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(FlairModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Flair {slug} not found")

    @model_validator(mode="after")
    def validate_flair_path(self) -> FlairModel:
        if not self.slug.strip():
            raise ValueError("Flair name cannot be empty or whitespace.")

        folder = self.sprite_type_override or self.category
        path = f"gfx/sprites/flairs/{folder}/{self.slug}.png"

        if not has.file(path):
            raise ValueError(
                f"No resource exists for flair name '{self.slug}' at path: {path}"
            )

        return self


class MonsterSpritesModel(BaseModel):
    front: str = Field(..., description="The front sprite")
    back: str = Field(..., description="The back sprite")
    menu1: str = Field(..., description="The menu1 sprite")
    menu2: str = Field(..., description="The menu2 sprite")

    # Validate resources that should exist
    @field_validator("front", "back")
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
    combat_call: Optional[SoundProperties] = Field(
        None, description="Sound configuration used when entering combat"
    )
    faint_call: Optional[SoundProperties] = Field(
        None, description="Sound configuration used when the monster faints"
    )


# Validate assignment allows us to assign a default inside a validator
class MonsterModel(BaseModel, BaseLookupModel, validate_assignment=True):
    table_name: ClassVar[str] = "monster"
    slug: str = Field(..., description="The slug of the monster")
    species: str = Field(..., description="The species of monster")
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
    types: Sequence[str] = Field(
        default_factory=list, description="The type(s) of this monster"
    )
    shape: str = Field(..., description="The shape of the monster")
    tags: Sequence[str] = Field(..., description="The tags of the monster")
    catch_rate: float = Field(
        ...,
        description="The catch rate of the monster",
        ge=prepare.CATCH_RATE_RANGE[0],
        le=prepare.CATCH_RATE_RANGE[1],
    )
    gender_weights: dict[GenderType, float] = Field(
        ..., description="Weighted gender probabilities for this monster"
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
        default_factory=list,
        description="The moveset of this monster",
        min_length=1,
    )
    history: Sequence[MonsterHistoryItemModel] = Field(
        default_factory=list,
        description="The evolution history of this monster",
    )
    evolutions: Sequence[MonsterEvolutionItemModel] = Field(
        default_factory=list, description="The evolutions this monster has"
    )
    flairs: set[str] = Field(
        default_factory=set, description="The flairs this monster has"
    )
    sounds: MonsterSoundsModel = Field(
        description="The sounds this monster has"
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> MonsterModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(MonsterModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Monster {slug} not found")

    # Set the default sprites based on slug. Specifying 'always' is needed
    # because by default pydantic doesn't validate null fields.
    @field_validator("sprites")
    def set_default_sprites(
        cls: MonsterModel, v: str, info: ValidationInfo
    ) -> Union[str, MonsterSpritesModel]:
        slug = info.data.get("slug")
        default = MonsterSpritesModel(
            front=f"gfx/sprites/battle/{slug}-front",
            back=f"gfx/sprites/battle/{slug}-back",
            menu1=f"gfx/sprites/battle/{slug}-menu01",
            menu2=f"gfx/sprites/battle/{slug}-menu02",
        )
        return v or default

    @field_validator("species")
    def translation_exists_species(cls: MonsterModel, v: str) -> str:
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

    @field_validator("gender_weights")
    def check_gender_weights(
        cls, v: dict[GenderType, float]
    ) -> dict[GenderType, float]:
        if not v:
            raise ValueError("gender_weights must contain at least one entry.")

        total = sum(v.values())
        if not isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(
                f"gender_weights must sum to 1.0, but got {total}"
            )

        return v

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

    @field_validator("flairs")
    def flair_exists(cls: MonsterModel, v: Sequence[str]) -> Sequence[str]:
        if v:
            for flair in v:
                if not has.db_entry("flair", flair):
                    raise ValueError(
                        f"the flair '{flair}' doesn't exist in the db"
                    )
        return v


class StatModel(BaseModel):
    value: float = Field(
        0.0,
        description="Direct value adjustment (used when step is not provided)",
    )
    step: Optional[int] = Field(
        None,
        description="Optional step delta to apply (e.g., +2 step to speed)",
        ge=-6,
        le=6,
    )
    max_deviation: int = Field(
        0,
        description="Maximum random deviation for the value or calculated step impact",
    )
    operation: str = Field(
        "+",
        description="Operation applied to stat (ignored if using step)",
    )
    overridetofull: bool = Field(
        False,
        description="If True and stat is HP, override current HP to full",
    )
    max_step_limit: float = Field(
        6.0,
        description="Maximum absolute value for stat steps used in nonlinear scaling (e.g., 6.0 for ±6)",
    )
    scaling_mode: str = Field(
        "nonlinear",
        description="Defines how step scaling is applied: 'linear' for base*(1+step), 'nonlinear' for tiered scaling",
    )


class Range(str, Enum):
    special = "special"
    melee = "melee"
    ranged = "ranged"
    touch = "touch"
    reach = "reach"
    reliable = "reliable"


class TechCategory(str, Enum):
    special = "special"
    animal = "animal"
    simple = "simple"
    basic = "basic"
    exotic = "exotic"
    reserved = "reserved"
    powerful = "powerful"
    condition_imposer = "condition_imposer"
    notype = "notype"


class StackingMode(str, Enum):
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"
    OVERRIDE = "override"


class ModifierAttribute(str, Enum):
    TYPE = "type"
    TAG = "tag"
    TERRAIN = "terrain"
    SHAPE = "shape"
    STAGE = "stage"
    SPECIES = "species"
    STAT = "stat"
    STAT_MAX = "stat_max"
    STAT_MIN = "stat_min"


class Modifier(BaseModel):
    attribute: ModifierAttribute = Field(
        ..., description="Attribute being modified (type, etc.)"
    )
    values: Sequence[str] = Field(
        default_factory=list,
        description="Values associated with the modification (e.g. fire, etc.)",
    )
    multiplier: float = Field(1.0, description="Multiplier", ge=0.0, le=2.0)
    priority: int = Field(
        0, description="Priority of the modifier. Higher wins."
    )
    stacking: StackingMode = Field(
        StackingMode.MULTIPLICATIVE,
        description="How this modifier stacks with others.",
    )
    max_stacks: Optional[int] = Field(
        None, description="Maximum number of stackable modifiers of this type"
    )
    condition_name: Optional[str] = Field(
        None,
        description="Name of a predefined condition function to determine applicability",
    )
    source: Optional[str] = Field(
        None, description="Origin of the modifier (e.g. move, item, ability)"
    )
    turns_remaining: Optional[int] = Field(
        None, description="Number of turns before modifier expires"
    )


class SpeedLabel(str, Enum):
    EXTREMELY_SLOW = "extremely_slow"
    VERY_SLOW = "very_slow"
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    VERY_FAST = "very_fast"
    EXTREMELY_FAST = "extremely_fast"

    @property
    def numeric_value(self) -> int:
        return {
            SpeedLabel.EXTREMELY_SLOW: -3,
            SpeedLabel.VERY_SLOW: -2,
            SpeedLabel.SLOW: -1,
            SpeedLabel.NORMAL: 0,
            SpeedLabel.FAST: 1,
            SpeedLabel.VERY_FAST: 2,
            SpeedLabel.EXTREMELY_FAST: 3,
        }[self]

    @classmethod
    def from_numeric(cls, value: int) -> SpeedLabel:
        for label in cls:
            if label.numeric_value == value:
                return label
        return cls.NORMAL


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


class TechniqueModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "technique"
    slug: str = Field(..., description="The slug of the technique")
    sort: TechSort = Field(..., description="The sort of technique this is")
    behaviors: TechBehaviors
    category: TechCategory = Field(
        ...,
        description="The tags of the technique",
    )
    tags: Sequence[str] = Field(
        ..., description="The tags of the technique", min_length=1
    )
    conditions: Sequence[LogicCondition] = Field(
        default_factory=list, description="Conditions that must be met"
    )
    effects: Sequence[ParameterizableRule] = Field(
        ..., description="Effects this technique uses"
    )
    target: TargetModel
    visuals: VisualProperties = Field(
        ..., description="Configuration for the technique's visual display."
    )
    sound: SoundProperties = Field(
        ..., description="Configuration for the technique's sound playback."
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
    confirm_text: str = Field(
        "item_confirm_use",
        description="Translation key for the label used when confirming tech usage.",
    )
    cancel_text: str = Field(
        "item_confirm_cancel",
        description="Translation key for the label used when canceling tech usage.",
    )
    menu_actions: Sequence[MenuAction] = Field(
        default_factory=list,
        description="Custom list of menu actions (key, display_text) for this technique.",
    )
    types: Sequence[str] = Field(
        default_factory=list, description="Type(s) of the technique"
    )
    power: float = Field(
        ...,
        description="Power of the technique",
        ge=prepare.POWER_RANGE[0],
        le=prepare.POWER_RANGE[1],
    )
    speed: SpeedLabel = Field(
        default=SpeedLabel.NORMAL,
        description=(
            "Indicates the relative speed of this technique. "
            "Possible values range from 'extremely_slow' to 'extremely_fast'."
        ),
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

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> TechniqueModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(TechniqueModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Technique {slug} not found")

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


class StepEffectType(str, Enum):
    NONE = "none"
    FLAT_DAMAGE = "flat_damage"
    PERCENT_MAX_HP_DAMAGE = "percent_max_hp_damage"
    PERCENT_CURRENT_HP_DAMAGE = "percent_current_hp_damage"
    PERCENT_MAX_HP_HEAL = "percent_max_hp_heal"
    PERCENT_CURRENT_HP_HEAL = "percent_current_hp_heal"


class StatusModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "status"
    slug: str = Field(..., description="The slug of the status")
    sort: TechSort = Field(..., description="The sort of status this is")
    behaviors: StatusBehaviors
    icon: str = Field(..., description="The icon to use for the condition")
    conditions: Sequence[LogicCondition] = Field(
        default_factory=list, description="Conditions that must be met"
    )
    effects: Sequence[ParameterizableRule] = Field(
        ..., description="Effects this status uses"
    )
    visuals: VisualProperties = Field(
        ..., description="Configuration for the status's visual display."
    )
    sound: SoundProperties = Field(
        ..., description="Configuration for the status's sound playback."
    )
    bond: bool = Field(
        False,
        description="Whether or not there is a bond between attacker and defender",
    )
    duration: int = Field(
        0, description="How many turns the status is supposed to last"
    )
    step_interval: int = Field(
        0,
        description="The number of steps between out-of-battle effect triggers.",
    )
    step_effect_value: float = Field(
        0.0,
        description="The value (flat or percentage) used for the step-interval effect.",
    )
    step_effect_type: StepEffectType = Field(
        StepEffectType.NONE,
        description="The type of effect triggered by the step interval.",
    )
    modifiers: list[Modifier] = Field(..., description="Various modifiers")

    # Optional fields
    category: Optional[CategoryStatus] = Field(
        None, description="Category status: positive or negative"
    )
    on_positive_status: Optional[ResponseStatus] = Field(
        None,
        description="Determines the response when a positive status is applied",
    )
    on_negative_status: Optional[ResponseStatus] = Field(
        None,
        description="Determines the response when a negative status is applied",
    )
    on_tech_use: Optional[str] = Field(
        None,
        description="Status applied after using a technique",
    )
    on_item_use: Optional[str] = Field(
        None,
        description="Status applied after using an item",
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
    cond_id: int = Field(..., description="The id of this status")
    stat_modifiers: dict[str, StatModel] = Field(
        default_factory=dict,
        description="Dictionary of stat modifiers keyed by stat name (e.g., 'speed', 'hp')",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> StatusModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(StatusModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Status {slug} not found")

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

    @field_validator("on_tech_use", "on_item_use")
    def status_exists(cls: StatusModel, v: Optional[str]) -> Optional[str]:
        if not v or has.db_entry("status", v) or has.db_entry("technique", v):
            return v
        raise ValueError(f"the status {v} doesn't exist in the db")


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
        default_factory=list,
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
        default_factory=list,
        description="List of variables that affect the item.",
        min_length=1,
    )

    @field_validator("slug")
    def item_exists(cls: BagItemModel, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")


class TemplateModel(BaseModel):
    slug: str = Field(
        ..., description="Slug uniquely identifying the template"
    )


class NpcTemplateModel(TemplateModel):
    sprite_name: str = Field(
        ..., description="Name of the overworld sprite filename"
    )
    combat_front: str = Field(
        ..., description="Name of the battle front sprite filename"
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


class DialogueContent(BaseModel):
    # This model holds all dialogue types
    greeting: Optional[Union[str, list[str]]] = Field(
        None, description="Greeting dialogue"
    )
    idle: Optional[Union[str, list[str]]] = Field(
        None, description="Idle chatter"
    )
    farewell: Optional[Union[str, list[str]]] = Field(
        None, description="Dialogue when saying goodbye"
    )
    pre_battle: Optional[Union[str, list[str]]] = Field(
        None, description="Dialogue before a battle"
    )
    post_battle_win: Optional[Union[str, list[str]]] = Field(
        None, description="Dialogue if NPC wins"
    )
    post_battle_lose: Optional[Union[str, list[str]]] = Field(
        None, description="Dialogue if NPC loses"
    )
    post_battle_draw: Optional[Union[str, list[str]]] = Field(
        None, description="Dialogue if battle is a draw"
    )

    @field_validator("*")
    def translation_exists(
        cls, v: Optional[Union[str, list[str]]]
    ) -> Optional[Union[str, list[str]]]:
        if not v:
            return v

        if isinstance(v, str):
            if not has.translation(v):
                raise ValueError(f"No translation exists with msgid: {v}")
        elif isinstance(v, list):
            for msgid in v:
                if not has.translation(msgid):
                    raise ValueError(
                        f"No translation exists with msgid: {msgid}"
                    )
        return v


class DialogueProfile(BaseModel):
    default: DialogueContent = Field(
        ..., description="The default dialogue for the NPC"
    )
    location_based: dict[str, DialogueContent] = Field(
        default_factory=dict,
        description="Overrides for dialogue based on location (map.tmx)",
    )

    def get_dialogue_for_location(self, location: str) -> DialogueContent:
        """Returns location-specific dialogue if available, otherwise default."""
        return self.location_based.get(location, self.default)


class NpcSpeech(BaseModel):
    profile: DialogueProfile = Field(
        ..., description="All dialogue for the NPC"
    )


class NpcCombatModel(BaseModel):
    forfeit: bool = Field(
        False,
        description="Whether the NPC allows the player to forfeit during combat",
    )
    switch_logic: Optional[str] = Field(
        None,
        description=(
            "Defines how the NPC selects a replacement monster when one faints. "
            "Examples include 'random', 'lv_highest', or 'healthiest'."
        ),
    )


class NpcAudioModel(BaseModel):
    battle_music: Optional[BattleMusicModel] = Field(
        None,
        description="Battle music configuration for the NPC; defaults to empty if not set",
    )


class NpcModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "npc"
    slug: str = Field(..., description="Slug of the name of the NPC")
    persistence: bool = Field(
        False,
        description="Whether this NPC should be retained and saved across sessions.",
    )
    template: NpcTemplateModel
    combat: NpcCombatModel
    monsters: Sequence[PartyMemberModel] = Field(
        default_factory=list, description="List of monsters in the NPCs party"
    )
    items: Sequence[BagItemModel] = Field(
        default_factory=list, description="List of items in the NPCs bag"
    )
    speech: NpcSpeech = Field(
        ...,
        description="Dialogue configuration for the NPC, including default lines and location-based overrides",
    )
    audio: NpcAudioModel = Field(
        ...,
        description="Audio configuration for the NPC, including music themes, sound effects, and ambient sounds",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> NpcModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(NpcModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"NPC {slug} not found")


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

    @field_validator("menu")
    def check_state(cls: BattleGraphicsModel, v: str) -> str:
        states = [state.name for state in State]
        if v in states:
            return v
        raise ValueError(f"state isn't among: {states}")


class BattleMusicModel(BaseModel):
    battle: MusicProperties = Field(
        ..., description="Music configuration used when fighting"
    )
    victory_music: MusicProperties = Field(
        ..., description="Music configuration used when winning"
    )
    defeat_music: MusicProperties = Field(
        ..., description="Music configuration used when losing"
    )


class EnvironmentModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "environment"
    slug: str = Field(..., description="Slug of the name of the environment")
    battle_graphics: BattleGraphicsModel
    battle_music: BattleMusicModel

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> EnvironmentModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(
                EnvironmentModel, db.lookup(slug, table=cls.table_name)
            )
        except EntryNotFoundError:
            raise RuntimeError(f"Encounter {slug} not found")


class HeldItemProbability(BaseModel):
    item_slug: str = Field(
        ..., description="Slug of the item that can be held."
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability (0.0-1.0) of this item being held.",
    )

    @field_validator("item_slug")
    def item_exists(cls, v: str) -> str:
        if not has.db_entry("item", v):
            raise ValueError(f"the item '{v}' doesn't exist in the db")
        return v


class EncounterItemModel(BaseModel):
    monster: str = Field(..., description="Monster slug for this encounter")
    encounter_rate: float = Field(
        ..., description="Probability of encountering this monster."
    )
    held_items: Sequence[HeldItemProbability] = Field(
        default_factory=list,
        description="A list of items that will be held with their probabilities.",
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
    level_offset: Optional[int] = Field(
        None,
        description="Offset (+/- levels) to apply to the monster's level.",
    )
    level_offset_range: Optional[tuple[int, int]] = Field(
        None,
        description="Range of offset (+/- levels) to apply randomly to base level.",
    )
    min_player_level: Optional[int] = Field(
        None,
        description="Minimum average level of player's party for this encounter.",
    )
    max_player_level: Optional[int] = Field(
        None,
        description="Maximum average level of player's party for this encounter.",
    )
    scaling_enabled: bool = Field(
        False,
        description="If true, scales the monster level based on player's party level average.",
    )
    override_level_range: bool = Field(
        False,
        description="If true, allows scaling to override a monster's declared level_range and match party average directly.",
    )
    scaling_offset_range: Optional[tuple[int, int]] = Field(
        None,
        description="Range used for random offset when scaling level overrides are applied (e.g. [-3, +4])",
    )

    @field_validator("monster")
    def monster_exists(cls: EncounterItemModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class HordeEncounterModel(BaseModel):
    monsters: Sequence[EncounterItemModel] = Field(
        ..., description="The list of monsters that make up this horde."
    )
    horde_level_range: Optional[Sequence[int]] = Field(
        None,
        description="Optional: A base level range for the entire horde. If set, individual monster `level_range` can be ignored or used as a modification.",
        max_length=2,
    )
    horde_exp_mod: Optional[float] = Field(
        None,
        description="Optional: A modifier for the experience points of the entire horde.",
        gt=0.0,
    )


class EncounterType(str, Enum):
    SINGLE = "single"
    HORDE = "horde"


class EncounterModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "encounter"
    slug: str = Field(
        ..., description="Slug to uniquely identify this encounter"
    )
    encounter_type: EncounterType = Field(
        EncounterType.SINGLE,
        description="The type of this encounter (single monster or a horde).",
    )
    monsters: Sequence[EncounterItemModel] = Field(
        default_factory=list, description="Monsters encounterable"
    )
    horde: Optional[HordeEncounterModel] = Field(
        None, description="Horde data (for horde encounters)"
    )
    scaling_zone: bool = Field(
        False,
        description="If true, this zone applies level scaling to all monsters",
    )
    scale_offset_range: Optional[tuple[int, int]] = Field(
        None,
        description="Custom offset range applied when scaling override is active (e.g. -3 to +5)",
    )
    scale_multiplier: float = Field(
        1.0,
        description="Multiplier applied to party average to define base scaled level",
    )
    override_level_range: bool = Field(
        False,
        description="If true, allows scaling to override a monster's declared level_range and match party average directly.",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> EncounterModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(EncounterModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Encounter {slug} not found")

    @model_validator(mode="after")
    def check_monster_horde_exclusivity(self) -> EncounterModel:
        has_monsters = bool(self.monsters)
        has_horde = self.horde is not None and bool(self.horde.monsters)

        if has_monsters and has_horde:
            raise ValueError(
                "Encounter cannot have both 'monsters' and 'horde' defined."
            )
        if not has_monsters and not has_horde:
            raise ValueError(
                "Encounter must define either 'monsters' or 'horde'."
            )
        return self


class DialogueModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "dialogue"
    slug: str = Field(
        ..., description="Slug to uniquely identify this dialogue"
    )
    bg_color: str = Field(..., description="RGB color (eg. 255:0:0)")
    font_color: str = Field(..., description="RGB color (eg. 255:0:0)")
    font_shadow_color: str = Field(..., description="RGB color (eg. 255:0:0)")
    border_slug: str = Field(..., description="Name of the border")
    border_path: str = Field(..., description="Path to the border")
    line_spacing: int = Field(0, description="Line spacing value")

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> DialogueModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(DialogueModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Dialogue {slug} not found")

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


class ElementModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "element"
    slug: str = Field(..., description="Slug uniquely identifying the type")
    icon: str = Field(..., description="The icon to use for the type")
    types: Sequence[ElementItemModel]

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> ElementModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(ElementModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Element {slug} not found")

    @field_validator("slug")
    def translation_exists_element(cls: ElementModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def sound_call_exists(cls: ElementModel, v: str) -> str:
        if has.db_entry("sounds", f"sound_{v}_call"):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")

    @field_validator("slug")
    def sound_faint_exists(cls: ElementModel, v: str) -> str:
        if has.db_entry("sounds", f"sound_{v}_faint"):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")

    @field_validator("icon")
    def file_exists(cls: ElementModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.ELEMENT_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")


class TasteModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "taste"
    slug: str = Field(..., description="Slug of the taste")
    name: str = Field(..., description="Name of the taste")
    taste_type: Literal["warm", "cold"] = Field(
        ..., description="Type of taste: 'cold' or 'warm'"
    )
    modifiers: Sequence[Modifier] = Field(
        ..., description="Modifiers associated with the taste"
    )
    rarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Rarity score between 0 (rare) and 1 (common)",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> TasteModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(TasteModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Taste {slug} not found")

    @field_validator("name")
    def translation_exists_taste(cls: TasteModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class EconomyEntityModel(BaseModel):
    price: int = Field(..., description="Price of the entity")
    cost: int = Field(..., description="Cost of the entity")
    inventory: int = Field(-1, description="Quantity of the entity")
    variables: Sequence[dict[str, str]] = Field(
        default_factory=list,
        description="List of variables that affect the entity in the economy.",
        min_length=1,
    )


class EconomyItemModel(EconomyEntityModel):
    slug: str = Field(..., description="Slug of the Item")
    inventory: int = Field(-1, description="Quantity of the entity")

    @field_validator("slug")
    def item_exists(cls: EconomyEntityModel, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")


class EconomyMonsterModel(EconomyEntityModel):
    slug: str = Field(..., description="Slug of the Monster")
    inventory: int = Field(1, description="Quantity of the entity", gt=0)
    level: int = Field(..., description="Level of the entity", gt=0)

    @field_validator("slug")
    def monster_exists(cls: EconomyEntityModel, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class EconomyModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "economy"
    slug: str = Field(..., description="Slug uniquely identifying the economy")
    resale_multiplier: float = Field(..., description="Resale multiplier")
    background: str = Field(..., description="Sprite used for background")
    items: Sequence[EconomyItemModel]
    monsters: Sequence[EconomyMonsterModel]

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> EconomyModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(EconomyModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Economy {slug} not found")

    @field_validator("background")
    def background_exists(cls: EconomyModel, v: str) -> str:
        if has.file(v) and has.size(v, prepare.NATIVE_RESOLUTION):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class FactionKind(str, Enum):
    GYM = "gym"
    TEAM = "team"
    LEAGUE = "league"
    CLUB = "club"
    VILLAGE = "village"
    ORGANIZATION = "organization"
    ELITE = "elite"
    ACADEMY = "academy"


class FactionAlignment(str, Enum):
    HEROIC = "heroic"
    VILLAINOUS = "villainous"
    ROGUE = "rogue"
    NEUTRAL = "neutral"
    CHAOTIC = "chaotic"
    LAWFUL = "lawful"


class FactionRelationStatus(str, Enum):
    ALLY = "ally"
    RIVAL = "rival"
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class RankRequirement(BaseModel):
    min_reputation: int = 0
    variables: Sequence[dict[str, Any]] = Field(
        default_factory=list,
        description="List of variables that affect the requirement.",
        min_length=1,
    )


class RankStep(BaseModel):
    title: str
    threshold: int
    requirement: Optional[RankRequirement] = None


class FactionModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "faction"

    slug: str = Field(..., description="Unique ID of the faction")
    kind: Optional[FactionKind] = Field(
        FactionKind.TEAM, description="Faction type (gym, team, league, etc.)"
    )
    alignment: Optional[FactionAlignment] = Field(
        None, description="Faction alignment: heroic, villainous, rogue, etc."
    )
    badge_id: Optional[str] = Field(
        None, description="Associated badge ID if applicable"
    )
    leader_char: Optional[str] = Field(
        None, description="Slug of the faction leader NPC"
    )
    ranks: list[RankStep] = Field(
        default_factory=lambda: [
            RankStep(title="Recruit", threshold=0),
            RankStep(title="Agent", threshold=50),
            RankStep(title="Elite", threshold=100),
        ],
        description="Rank steps based on reputation",
    )
    members: list[str] = Field(
        default_factory=list,
        description="NPC slugs that belong to this faction",
    )
    reputation: dict[str, int] = Field(
        default_factory=dict,
        description="Reputation scores for NPC members, used for rank evaluation and internal hierarchy",
    )
    relations: dict[str, FactionRelationStatus] = Field(
        default_factory=dict, description="Relationships with other factions"
    )
    public_reputation: int = Field(
        0, description="General public reputation score of the faction."
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> FactionModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(FactionModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Mission {slug} not found")

    @field_validator("slug")
    def translation_exists_faction(cls: FactionModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("members")
    def member_exists(cls: FactionModel, v: Sequence[str]) -> Sequence[str]:
        for npc_slug in v:
            if not has.db_entry("npc", npc_slug):
                raise ValueError(
                    f"The npc '{npc_slug}' doesn't exist in the db"
                )
        return v

    @field_validator("leader_char")
    def leader_exists(cls: FactionModel, v: Optional[str]) -> Optional[str]:
        if v:
            if not has.db_entry("npc", v):
                raise ValueError(f"The npc '{v}' doesn't exist in the db")
        return v

    @model_validator(mode="before")
    def validate_faction_integrity(
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        members = values.get("members", [])
        reputation = values.get("reputation", {})
        leader = values.get("leader_char")

        missing_reputation = [m for m in members if m not in reputation]
        if missing_reputation:
            raise ValueError(
                f"Missing reputation entries for members: {', '.join(missing_reputation)}"
            )

        if leader and leader not in members:
            raise ValueError(
                f"Faction leader '{leader}' must also be a member."
            )

        if leader and leader not in reputation:
            raise ValueError(
                f"Faction leader '{leader}' is missing a reputation score."
            )

        return values

    @model_validator(mode="after")
    def validate_unique_rank_thresholds(self) -> FactionModel:
        thresholds = [rank.threshold for rank in self.ranks]
        if len(thresholds) != len(set(thresholds)):
            raise ValueError(
                "All rank thresholds must be unique within a faction."
            )
        return self


class MissionStepModel(BaseModel):
    slug: str = Field(..., description="Unique identifier for the step")
    order: int = Field(
        default=0,
        description="Progression order index used to sequence mission steps",
    )
    description: str = Field(
        ..., description="Describes what the step requires or represents"
    )
    conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Simple conditions on game_variables (all must be true)",
    )
    any_of: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Alternative condition sets; step completes if any are satisfied",
    )
    all_of: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Additional condition sets; all must be satisfied",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Slugs of next steps unlocked when this is completed",
    )
    step_items_needed: dict[str, Optional[int]] = Field(
        default_factory=dict,
        description="Items required to complete this step. Quantity is optional; None means at least one.",
    )
    step_monsters_needed: dict[str, Optional[int]] = Field(
        default_factory=dict,
        description="Monsters required to complete this step. Level is optional; None means any level.",
    )
    optional: bool = Field(False, description="Whether the step is optional")


class MissionModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "mission"

    slug: str = Field(..., description="Slug uniquely identifying the mission")
    description: str = Field(
        ..., description="Detailed description of the mission objectives"
    )
    prerequisites: Sequence[dict[str, Any]] = Field(
        default_factory=list,
        description="List of game variables required to unlock the mission",
    )
    connected_missions: Sequence[dict[str, Any]] = Field(
        default_factory=list,
        description="List of missions that this one unlocks",
    )
    required_items: dict[str, Optional[int]] = Field(
        default_factory=dict,
        description="Items required to begin the mission with optional quantity. None means at least one.",
    )
    required_monsters: dict[str, Optional[int]] = Field(
        default_factory=dict,
        description="Monsters required to begin the mission with optional minimum level. None means any level.",
    )
    required_missions: Sequence[str] = Field(
        default_factory=list,
        description="Slugs of missions that must be completed before this one",
    )
    steps: dict[str, MissionStepModel] = Field(
        default_factory=dict,
        description="Dictionary of steps defining structure and branching logic",
    )
    repeatable: bool = Field(
        False, description="Whether the mission can be repeated"
    )
    failure_conditions: Sequence[dict[str, Any]] = Field(
        default_factory=list,
        description="List of game variables that, if met, cause the mission to fail",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> MissionModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(MissionModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Mission {slug} not found")

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
    def item_exists(
        cls: MissionModel, v: dict[str, Optional[int]]
    ) -> dict[str, Optional[int]]:
        for item_slug in v.keys():
            if not has.db_entry("item", item_slug):
                raise ValueError(
                    f"The item '{item_slug}' doesn't exist in the db"
                )
        return v

    @field_validator("required_monsters")
    def monster_exists(
        cls: MissionModel, v: dict[str, Optional[int]]
    ) -> dict[str, Optional[int]]:
        for monster_slug in v.keys():
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


class AnimationModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "animation"
    slug: str = Field(..., description="Unique slug for the animation")
    file: str = Field(..., description="File of the animation")
    duration: float = Field(
        default=0.1,
        description="Duration (in seconds) for each frame of the animation.",
    )
    loop: int = Field(
        default=-1,
        description=(
            "Number of times the visual should loop. "
            "-1 means infinite looping, 0 means play once, "
            "any positive integer means loop that many times."
        ),
    )
    rate: float = Field(
        default=1.0,
        description="Playback speed multiplier. 1.0 is normal speed; higher values play faster.",
    )
    flip_axes: FlipAxes = Field(
        default=FlipAxes.NONE,
        description="Axes to flip the animation frames. Options: '', 'x', 'y', or 'xy'.",
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> AnimationModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(AnimationModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Animation {slug} not found")

    @field_validator("file")
    def file_exists(cls: AnimationModel, v: str, info: ValidationInfo) -> str:
        slug = info.data.get("slug")
        file: str = f"animations/{v}/{slug}_00.png"
        if has.file(file):
            return v
        raise ValueError(f"the animation {v} doesn't exist in the db")

    @field_validator("duration")
    def validate_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class TerrainModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "terrain"
    slug: str = Field(..., description="Slug of the terrain")
    name: str = Field(..., description="Name of the terrain condition")
    modifiers: list[Modifier] = Field(..., description="Various modifiers")

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> TerrainModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(TerrainModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Terrain {slug} not found")

    @field_validator("name")
    def translation_exists_item(cls: TerrainModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class WeatherModel(BaseModel, BaseLookupModel):
    table_name: ClassVar[str] = "weather"
    slug: str = Field(..., description="Slug of the weather")
    name: str = Field(..., description="Name of the weather condition")
    temperature: Temperature = Field(
        ...,
        description="The general temperature category for this weather state.",
    )
    wind: Wind = Field(
        ...,
        description="The general wind intensity level for this weather state.",
    )
    modifiers: list[Modifier] = Field(..., description="Various modifiers")

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> WeatherModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(WeatherModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Weather {slug} not found")

    @field_validator("name")
    def translation_exists_item(cls: WeatherModel, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


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
    FlairModel,
    MusicModel,
    AnimationModel,
    NpcModel,
    SoundModel,
    StatusModel,
    TechniqueModel,
    FactionModel,
]


def load_model_map(
    model_map_config: dict[str, str],
) -> dict[str, type[DataModel]]:
    model_map: dict[str, type[DataModel]] = {}
    for table, model_path in model_map_config.items():
        module_name, class_name = model_path.rsplit(".", 1)
        module = import_module(module_name)
        model_map[table] = getattr(module, class_name)
    return model_map


fetch_mod_asset_roots(prepare.CONFIG)
path = fetch_asset(mods_folder.as_posix(), "db_config.yaml")
config = load_config(path)
model_map = load_model_map(config.model_map)
loader = ModelLoader(model_map)
# Global database container
db = ModData(config, loader)
# Validator container
has = Validator(db)
