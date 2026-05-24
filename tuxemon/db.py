# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum, auto
from importlib import import_module
from math import isclose
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    TypeVar,
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

from tuxemon.database.config import EntryNotFoundError
from tuxemon.database.data import ModData
from tuxemon.database.registry import validator as has
from tuxemon.database.rules import config_monster
from tuxemon.platform.const import sizes
from tuxemon.surfanim import FlipAxes

logger = logging.getLogger(__name__)


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class FacingMode(Enum):
    FOLLOW_MOVEMENT = auto()
    LOCKED = auto()
    SCRIPTED = auto()


class Orientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class ItemSort(str, Enum):
    POTION = "potion"
    UTILITY = "utility"
    QUEST = "quest"


class PlagueType(str, Enum):
    INOCULATED = "inoculated"
    INFECTED = "infected"
    CARRIER = "carrier"
    RECOVERED = "recovered"


class GenderType(str, Enum):
    NEUTER = "neuter"
    MALE = "male"
    FEMALE = "female"


class SkinSprite(str, Enum):
    LIGHT = "light"
    TANNED = "tanned"
    DARK = "dark"
    ALBINO = "albino"
    ORC = "orc"


class ItemRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ItemCategory(str, Enum):
    NONE = "none"
    BADGE = "badge"
    ELEMENTS = "elements"
    FOSSIL = "fossil"
    MORPH = "morph"
    POTION = "potion"
    TECHNIQUE = "technique"
    PHONE = "phone"
    FISH = "fish"
    DESTROY = "destroy"
    CAPTURE = "capture"
    STATS = "stats"
    FOOD = "food"
    DOLL = "doll"


class OutputBattle(str, Enum):
    WON = "won"
    LOST = "lost"
    DRAW = "draw"


class SeenStatus(str, Enum):
    UNSEEN = "unseen"
    SEEN = "seen"
    CAUGHT = "caught"


class StatType(str, Enum):
    ARMOUR = "armour"
    DODGE = "dodge"
    HP = "hp"
    MELEE = "melee"
    RANGED = "ranged"
    SPEED = "speed"


class EvolutionStage(str, Enum):
    STANDALONE = "standalone"
    BASIC = "basic"
    STAGE1 = "stage1"
    STAGE2 = "stage2"


class MissionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REMOVED = "removed"


class MusicStatus(str, Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


class Comparison(str, Enum):
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    GREATER_THAN = "greater_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"


class TargetType(str, Enum):
    ENEMY_MONSTER = "enemy_monster"
    OWN_MONSTER = "own_monster"
    ENEMY_TEAM = "enemy_team"
    OWN_TEAM = "own_team"
    ENEMY_TRAINER = "enemy_trainer"
    OWN_TRAINER = "own_trainer"


class Temperature(str, Enum):
    FREEZING = "freezing"
    COLD = "cold"
    MILD = "mild"
    WARM = "warm"
    HOT = "hot"
    SCORCHING = "scorching"


class Wind(str, Enum):
    CALM = "calm"
    BREEZY = "breezy"
    WINDY = "windy"
    GUSTY = "gusty"
    STORMY = "stormy"


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


class LoopMode(Enum):
    INFINITE = -1  # loop forever
    NO_LOOP = 0  # play once


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


class DataModel(BaseModel):
    """Marker base class for models that belong in the database."""

    slug: str


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


class Behavior(BaseModel):
    type: str = Field(..., description="Behavior type identifier.")
    args: Sequence[str] = Field(default_factory=list)
    name: str = Field("unnamed_behavior")


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
    timeout: float | None = Field(
        None,
        description="Maximum duration (in seconds) this event is allowed to run. None = no timeout.",
    )
    delay: float | None = Field(
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
    behavs: Sequence[Behavior] = Field(
        default_factory=list,
        description="Behavior definitions attached to this event.",
    )


class BaseComparison(BaseModel):
    comparison: Comparison = Field(
        ...,
        description="The type of comparison to perform (e.g., greater_than, equal_to).",
    )
    target_value: int | None = Field(
        None,
        description="An optional fixed numeric value to compare against (e.g., stat must be greater than 50).",
    )


class StatsComparison(BaseComparison):
    stat_type: StatType = Field(
        ...,
        description="The primary stat being evaluated for the evolution condition (e.g., speed, defense).",
    )
    target_stat: StatType | None = Field(
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


class GameCondition(BaseModel):
    """
    A generic condition requirement used across Economy, Quests, and NPCs.
    """

    key: str = Field(..., description="The internal variable name to check.")
    value: Any = Field(
        ..., description="The value required to pass the check."
    )
    scope: str | None = Field(
        default=None,
        description="Optional scope: 'player' or 'world'. Checks both if None.",
    )
    description: str | None = Field(
        default=None,
        description="A human-readable explanation of the requirement for debugging.",
    )


class PartyConditionsModel(BaseModel):
    monster_slugs: dict[str, int] | None = Field(
        None,
        description="A dictionary specifying required monsters and their minimum counts by slug.",
    )
    monster_types: dict[str, int] | None = Field(
        None,
        description="A dictionary specifying required monster types and their minimum counts.",
    )
    genders: dict[GenderType, int] | None = Field(
        None,
        description="A dictionary specifying required genders and their minimum counts.",
    )
    alignment: str | None = Field(
        None,
        description="The elemental alignment the party must lean toward for evolution to occur.",
    )
    party_size: int | None = Field(
        None,
        ge=1,
        le=sizes.PARTY_LIMIT,
        description="Required number of monsters in the party.",
    )
    party_level: int | None = Field(
        None,
        ge=1,
        description="Minimum average level of monsters in the party.",
    )
    party_stages: dict[str, int] | None = Field(
        None,
        description="Required evolution stages and their minimum counts (e.g. {'stage2': 2}).",
    )

    @model_validator(mode="after")
    def at_least_one_condition(self) -> PartyConditionsModel:
        if not any(
            [
                self.monster_slugs,
                self.monster_types,
                self.genders,
                self.alignment,
                self.party_size,
                self.party_level,
                self.party_stages,
            ]
        ):
            raise ValueError("At least one party condition must be specified.")
        return self

    @field_validator("party_stages")
    def validate_party_stages(
        cls, v: dict[str, int] | None
    ) -> dict[str, int] | None:
        if v:
            valid_stages = {stage.value for stage in EvolutionStage}
            for stage, count in v.items():
                if stage not in valid_stages:
                    raise ValueError(
                        f"Evolution stage '{stage}' is not valid. Must be one of {valid_stages}."
                    )
                if not (1 <= count < sizes.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for stage '{stage}' must be between 1 and {sizes.PARTY_LIMIT - 1}."
                    )
        return v

    @field_validator("monster_slugs")
    def validate_monster_slugs(
        cls, v: dict[str, int] | None
    ) -> dict[str, int] | None:
        if v:
            for slug, count in v.items():
                if not has.db_entry("monster", slug):
                    raise ValueError(
                        f"Monster slug '{slug}' does not exist in the database."
                    )
                if not (1 <= count < sizes.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for monster slug '{slug}' must be between 1 and {sizes.PARTY_LIMIT - 1}."
                    )
        return v

    @field_validator("monster_types")
    def validate_monster_types(
        cls, v: dict[str, int] | None
    ) -> dict[str, int] | None:
        if v:
            for type_, count in v.items():
                if not has.db_entry("element", type_):
                    raise ValueError(
                        f"Monster type '{type_}' does not exist in the database."
                    )
                if not (1 <= count < sizes.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for monster type '{type_}' must be between 1 and {sizes.PARTY_LIMIT - 1}."
                    )
        return v

    @field_validator("genders")
    def validate_genders(
        cls, v: dict[GenderType, int] | None
    ) -> dict[GenderType, int] | None:
        if v:
            for gender, count in v.items():
                if not (1 <= count < sizes.PARTY_LIMIT):
                    raise ValueError(
                        f"Count for gender '{gender}' must be between 1 and {sizes.PARTY_LIMIT - 1}."
                    )
        return v

    @field_validator("alignment")
    def validate_alignment(cls, v: str | None) -> str | None:
        if not v or has.db_entry("element", v):
            return v
        raise ValueError(f"Alignment '{v}' does not exist in the database.")


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
    def translation_exists(cls, v: str) -> str:
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
    destroy_on_break: bool = Field(
        False,
        description="Whether the item is removed from the inventory when it breaks.",
    )
    wear_on_use: bool = Field(
        False, description="Whether using this item increases its wear."
    )
    block_evolution: bool = Field(
        False,
        description="Whether or not this item prevents the holder from evolving.",
    )


class TechBehaviors(Behaviors):
    """Behaviors specific to techniques."""

    is_field_tech: bool = Field(
        False,
        description="Whether this technique can be used in the overworld.",
    )
    bypasses_selection: bool = Field(
        False,
        description="Whether this technique skips target selection and applies directly to the user's monster.",
    )


class StatusBehaviors(Behaviors):
    """Behaviors specific to statuses."""

    persists_after_combat: bool = Field(
        False,
        description="Whether this status effect remains active after combat ends.",
    )


class SoundProperties(BaseModel):
    sfx: str | None = Field(..., description="Sound effect to play")
    volume: float = Field(..., ge=0.0, description="Playback volume")

    @field_validator("sfx")
    def sfx_exists(cls, v: str | None) -> str | None:
        if not v:
            return v

        if has.db_entry("sounds", v):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class MusicProperties(BaseModel):
    music: str | None = Field(..., description="Music to play")

    @field_validator("music")
    def music_exists(cls, v: str | None) -> str | None:
        if not v:
            return v

        if has.db_entry("music", v):
            return v
        raise ValueError(f"the music {v} doesn't exist in the db")


class VisualProperties(BaseModel):
    animation: str | None = Field(
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

    def loop_mode(self) -> LoopMode | int:
        if self.loop == -1:
            return LoopMode.INFINITE
        if self.loop == 0:
            return LoopMode.NO_LOOP
        return self.loop  # positive integer = loop N times

    @field_validator("animation")
    def animation_exists(cls, v: str | None) -> str | None:
        if not v:
            return v

        item_file = f"animations/item/{v}.png"
        technique_file = f"animations/technique/{v}.png"

        if has.db_entry("animation", v) and (
            has.file(item_file) or has.file(technique_file)
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


class ItemModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "item"
    _lookup_cache: ClassVar[dict[str, ItemModel]] = {}
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
    dynamic_menu: DynamicMenuEntry | None = Field(
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
    stat_modifiers: dict[str, StatModel] = Field(
        default_factory=dict,
        description="Dictionary of stat modifiers keyed by stat name (e.g., 'speed', 'hp')",
    )
    immunity_to_status: Sequence[str] = Field(
        default_factory=list,
        description="Statuses this item grants immunity to",
    )
    granted_techniques: Sequence[str] = Field(
        default_factory=list,
        description="Technique slugs granted to the holder while this item is equipped.",
    )
    granted_statuses: Sequence[str] = Field(
        default_factory=list,
        description="Status slugs granted to the holder while this item is equipped.",
    )
    break_into_item: str | None = Field(
        None, description="Slug of the item created when this one breaks."
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> ItemModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(ItemModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Item {slug} not found")

    @classmethod
    def load_cache(cls, db: ModData) -> None:
        """Populate the internal cache if it hasn't been populated yet."""
        if not cls._lookup_cache:
            cls._lookup_cache = {
                tech_name: result
                for tech_name in db.database[cls.table_name]
                if (result := cls.lookup(tech_name, db))
            }

    @classmethod
    def get_cache(cls) -> dict[str, ItemModel]:
        """Returns the current cache."""
        return cls._lookup_cache

    @field_validator("use_item", "use_success", "use_failure")
    def translation_exists(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_item(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("sprite")
    def file_exists(cls, v: str) -> str:
        if has.file(v) and has.size(v, sizes.ITEM_SIZE):
            return v
        raise ValueError(f"the sprite {v} doesn't exist in the db")

    @field_validator("immunity_to_status")
    def status_exists(cls, v: Sequence[str]) -> Sequence[str]:
        if v:
            for status in v:
                if status != "all" and not has.db_entry("status", status):
                    raise ValueError(
                        f"A status {status} doesn't exist in the db"
                    )
        return v

    @field_validator("granted_techniques")
    def techniques_exist(cls, v: Sequence[str]) -> Sequence[str]:
        for tech in v:
            if not has.db_entry("technique", tech):
                raise ValueError(
                    f"Technique {tech} does not exist in the database"
                )
        return v

    @field_validator("granted_statuses")
    def statuses_exist(cls, v: Sequence[str]) -> Sequence[str]:
        for status in v:
            if not has.db_entry("status", status):
                raise ValueError(
                    f"Status {status} does not exist in the database"
                )
        return v

    @field_validator("break_into_item")
    def break_item_exists(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not has.db_entry("item", v):
            raise ValueError(
                f"Break-into item '{v}' does not exist in the database"
            )
        return v


class AttributesModel(BaseModel):
    armour: int = Field(..., description="Armour value")
    dodge: int = Field(..., description="Dodge value")
    hp: int = Field(..., description="HP (Hit Points) value")
    melee: int = Field(..., description="Melee value")
    ranged: int = Field(..., description="Ranged value")
    speed: int = Field(..., description="Speed value")


class ShapeModel(DataModel, BaseLookupModel):
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
    def translation_exists_shape(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class LearningMethod(str, Enum):
    LEVEL_UP = "level_up"
    TM = "tm"
    EVENT = "event"
    EVOLUTION = "evolution"
    FALLBACK = "fallback"


class MonsterMovesetItemModel(BaseModel):
    level_learned: int = Field(
        ..., description="Monster level in which this moveset is learned", gt=0
    )
    technique: str = Field(
        ...,
        description="Name of the technique for this moveset item",
    )
    evolution_stage_learned: EvolutionStage | None = Field(
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
    def technique_exists(cls, v: str) -> str:
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
    def validate_monsters_exist(cls, v: str | list[str]) -> str | list[str]:
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
    at_level: int | None = Field(
        None,
        description="The level at which the monster evolves.",
        ge=1,
    )
    element: str | None = Field(
        None,
        description="The element type that the monster must match to evolve.",
    )
    gender: GenderType | None = Field(
        None,
        description="The required gender of the monster for evolution.",
    )
    item: dict[str, float] | None = Field(
        None,
        description=(
            "A dictionary of item slugs and their associated evolution weights. "
            "Weights are relative and will be normalized to sum to 1.0. "
            "Each item must exist in the database and have a non-negative weight."
        ),
    )
    inside: bool | None = Field(
        None,
        description="Whether the monster must be inside to evolve.",
    )
    acquisition: Acquisition | None = Field(
        None,
        description="How the monster was obtained (e.g. caught, bred, traded, gifted).",
    )
    variables: Sequence[GameCondition] = Field(
        default_factory=list,
        description="The game variables that must exist and match a specific value for the monster to evolve.",
    )
    stats: StatsComparison | None = Field(
        None,
        description=(
            "Defines a condition where one monster stat must compare to another stat or value "
            "for evolution to occur. For example, 'speed must be greater than defense'. "
            "Includes the stat being evaluated, the type of comparison (e.g., greater_than, equal_to), "
            "and the target stat or value."
        ),
    )
    steps: int | None = Field(
        None,
        description="The minimum number of steps the monster must have walked to evolve.",
        ge=1,
    )
    tech: str | None = Field(
        None,
        description="The technique that a monster in the party must have for the evolution to occur.",
    )
    moves: Sequence[str] = Field(
        default_factory=list,
        description="The techniques that the monster must have learned for the evolution to occur.",
    )
    bond: BondComparison | None = Field(
        None,
        description=(
            "Defines a condition where the monster's bond must meet a specific comparison to evolve. "
            "Includes the comparison type (e.g., greater_than, equals) and the target bond value. "
            "For example, 'bond must be greater than 50'."
        ),
    )
    tastes: dict[str, str] | None = Field(
        None,
        description="A dictionary of taste values required for the monster to evolve (e.g., {'cold': 'value', 'warm': 'value'}).",
    )
    probability: float | None = Field(
        None,
        description="Chance (0.0 to 1.0) that this evolution occurs when conditions are met.",
        ge=0.0,
        le=1.0,
    )
    held_item: str | None = Field(
        None, description="Item slug the monster must be holding to evolve."
    )
    party_conditions: PartyConditionsModel | None = Field(
        None,
        description="Complex conditions based on the player's party required for evolution.",
    )

    @field_validator("moves")
    def validate_moves(cls, v: Sequence[str]) -> Sequence[str]:
        if not v:
            raise ValueError("Moves must contain at least 1 technique.")
        for slug in v:
            if not has.db_entry("technique", slug):
                raise ValueError(
                    f"the technique '{slug}' doesn't exist in the db."
                )
        return v

    @field_validator("tech")
    def technique_exists(cls, v: str | None) -> str | None:
        if not v or has.db_entry("technique", v):
            return v
        raise ValueError(f"the technique {v} doesn't exist in the db")

    @field_validator("tastes")
    def validate_tastes(
        cls, v: dict[str, str] | None
    ) -> dict[str, str] | None:
        if v:
            for taste_value in v.values():
                if not has.db_entry("taste", taste_value):
                    raise ValueError(
                        f"the taste '{taste_value}' does not exist in the database."
                    )
        return v

    @field_validator("element")
    def element_exists(cls, v: str | None) -> str | None:
        if not v or has.db_entry("element", v):
            return v
        raise ValueError(f"the element {v} doesn't exist in the db")

    @field_validator("monster_slug")
    def monster_exists(cls, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")

    @field_validator("item")
    def validate_item_and_weights(
        cls, v: dict[str, float] | None
    ) -> dict[str, float] | None:
        if v is None:
            return v

        total_weight = 0.0
        for item_slug, weight in v.items():
            if not has.db_entry("item", item_slug):
                raise ValueError(
                    f"The item '{item_slug}' does not exist in the database."
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
        logger.debug(f"Item weights normalized: {normalized}")
        return normalized

    @field_validator("held_item")
    def held_item_exists(cls, v: str | None) -> str | None:
        if not v or has.db_entry("item", v):
            return v
        raise ValueError(f"the held item {v} doesn't exist in the db")


class FlairModel(DataModel, BaseLookupModel):
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
    x_offset: int | None = Field(
        None,
        description="The horizontal offset of the flair from the sprite's origin.",
    )
    y_offset: int | None = Field(
        None,
        description="The vertical offset of the flair from the sprite's origin.",
    )
    sprite_type: set[str] | None = Field(
        None,
        description="Specifies which sprite type this flair applies to (e.g., 'front', 'back', 'menu01'). If None, applies to all.",
    )
    sprite_type_override: str | None = Field(
        None,
        description="Overrides the default sprite type used in the file path (e.g., 'universal').",
    )
    color: ColorModel | None = Field(
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
    sheet: str  # Path to the combined sprite sheet
    # Front sprite region
    front_rect: tuple[int, int, int, int] = (0, 0, 64, 64)
    # Back sprite region
    back_rect: tuple[int, int, int, int] = (64, 0, 64, 64)
    # Menu icon 1 region
    menu1_rect: tuple[int, int, int, int] = (0, 64, 24, 24)
    # Menu icon 2 region
    menu2_rect: tuple[int, int, int, int] = (24, 64, 24, 24)

    @field_validator("sheet")
    def sheet_exists(cls, v: str) -> str:
        if has.file(f"{v}.png"):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class MonsterSoundsModel(BaseModel):
    combat_call: SoundProperties | None = Field(
        None, description="Sound configuration used when entering combat"
    )
    faint_call: SoundProperties | None = Field(
        None, description="Sound configuration used when the monster faints"
    )


class MonsterModel(DataModel, BaseLookupModel, validate_assignment=True):
    table_name: ClassVar[str] = "monster"
    _lookup_cache: ClassVar[dict[str, MonsterModel]] = {}
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
    sprites: Annotated[
        MonsterSpritesModel | None, Field(validate_default=True)
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
        ge=config_monster.catch_rate_range[0],
        le=config_monster.catch_rate_range[1],
    )
    gender_weights: dict[GenderType, float] = Field(
        ..., description="Weighted gender probabilities for this monster"
    )
    lower_catch_resistance: float = Field(
        ...,
        description="The lower catch resistance of the monster",
        ge=config_monster.catch_resistance_range[0],
        le=config_monster.catch_resistance_range[1],
    )
    upper_catch_resistance: float = Field(
        ...,
        description="The upper catch resistance of the monster",
        ge=config_monster.catch_resistance_range[0],
        le=config_monster.catch_resistance_range[1],
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
    max_moves: int = Field(
        default=config_monster.max_moves,
        description="Maximum number of moves this monster can know",
        ge=1,
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> MonsterModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(MonsterModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Monster {slug} not found")

    @classmethod
    def load_cache(cls, db: ModData) -> None:
        """Populates the internal cache if it hasn't been populated yet."""
        if not cls._lookup_cache:
            cls._lookup_cache = {
                mon_name: result
                for mon_name in db.database[cls.table_name]
                if (result := cls.lookup(mon_name, db)).txmn_id > 0
            }

    @classmethod
    def get_cache(cls) -> dict[str, MonsterModel]:
        """Returns the current cache."""
        return cls._lookup_cache

    def can_evolve_at_level(self, level: int) -> bool:
        return any(
            evo.at_level is not None and evo.at_level <= level
            for evo in self.evolutions
        )

    def is_underleveled_for_form(self, level: int, db: ModData) -> bool:
        """
        Checks if this monster's current form is only possible at a
        higher level than the one provided by checking its ancestors.
        """
        current_history = next(
            (h for h in self.history if h.slug == self.slug), None
        )

        if not current_history or not current_history.evolves_from:
            return False

        for parent_slug in current_history.evolves_from:
            try:
                parent_mon = MonsterModel.lookup(parent_slug, db)
            except RuntimeError:
                continue  # Skip if parent data is missing

            for evo in parent_mon.evolutions:
                if evo.monster_slug == self.slug:
                    if evo.at_level is not None and level < evo.at_level:
                        return True

        return False

    @field_validator("sprites")
    def set_default_sprites(
        cls,
        v: MonsterSpritesModel | None,
        info: ValidationInfo,
    ) -> MonsterSpritesModel:
        slug = info.data.get("slug")
        default = MonsterSpritesModel(sheet=f"gfx/sprites/battle/{slug}-sheet")
        return v or default

    @field_validator("species")
    def translation_exists_species(cls, v: str) -> str:
        if has.translation(f"cat_{v}"):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("types")
    def element_exists(cls, elements: Sequence[str]) -> Sequence[str]:
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
    def shape_exists(cls, v: str) -> str:
        if has.db_entry("shape", v):
            return v
        raise ValueError(f"the shape {v} doesn't exist in the db")

    @field_validator("terrains")
    def terrain_exists(cls, v: Sequence[str]) -> Sequence[str]:
        if v:
            for terrain in v:
                if not has.db_entry("terrain", terrain):
                    raise ValueError(
                        f"the terrain '{terrain}' doesn't exist in the db"
                    )
        return v

    @field_validator("flairs")
    def flair_exists(cls, v: Sequence[str]) -> Sequence[str]:
        if v:
            for flair in v:
                if not has.db_entry("flair", flair):
                    raise ValueError(
                        f"the flair '{flair}' doesn't exist in the db"
                    )
        return v

    @model_validator(mode="after")
    def must_have_fallback(self) -> MonsterModel:
        if not any(
            m.learning_method == LearningMethod.FALLBACK for m in self.moveset
        ):
            raise ValueError(
                "Monster must define at least one fallback technique."
            )
        return self


class StatModel(BaseModel):
    value: float = Field(
        0.0,
        description="Direct value adjustment (used when step is not provided)",
    )
    step: int | None = Field(
        None,
        description="Optional step delta to apply (e.g., +2 step to speed)",
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

    @field_validator("step")
    def validate_step(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if not (-6 <= v <= 6):
            raise ValueError("step must be between -6 and 6")
        return v


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
    max_stacks: int | None = Field(
        None, description="Maximum number of stackable modifiers of this type"
    )
    condition_name: str | None = Field(
        None,
        description="Name of a predefined condition function to determine applicability",
    )
    source: str | None = Field(
        None, description="Origin of the modifier (e.g. move, item, ability)"
    )
    turns_remaining: int | None = Field(
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
    NEGATIVE = "negative"
    POSITIVE = "positive"
    NEUTRAL = "neutral"


class ResponseStatus(str, Enum):
    REPLACED = "replaced"
    REMOVED = "removed"
    STACKED = "stacked"


class BlockedReason(str, Enum):
    IMMUNE = "immune"
    IMMUNE_BY_ITEM = "immune_by_item"
    ALREADY_PRESENT = "already_present"
    REPLACED = "replaced"
    REMOVED = "removed"
    NO_EFFECT = "no_effect"


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
    def validate_bool_field(cls, v: bool) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f"One of the targets {v} isn't a boolean")
        return v


class TechniqueModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "technique"
    _lookup_cache: ClassVar[dict[str, TechniqueModel]] = {}
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
    stat_modifiers: dict[str, StatModel] = Field(
        default_factory=dict,
        description="Dictionary of stat modifiers keyed by stat name (e.g., 'speed', 'hp')",
    )
    use_tech: str | None = Field(
        None,
        description="Slug of what string to display when technique is used",
    )
    use_success: str | None = Field(
        None,
        description="Slug of what string to display when technique succeeds",
    )
    use_failure: str | None = Field(
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
        ge=sizes.POWER_RANGE[0],
        le=sizes.POWER_RANGE[1],
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
        ge=sizes.HEALING_POWER_RANGE[0],
        le=sizes.HEALING_POWER_RANGE[1],
    )
    recharge: int = Field(
        0,
        description="The base number of turns it takes to recharge after use.",
        ge=sizes.RECHARGE_RANGE[0],
        le=sizes.RECHARGE_RANGE[1],
    )
    min_recharge: int = Field(
        0,
        description="The absolute floor for recharge time (haste/multipliers cannot go below this).",
        ge=0,
    )
    initial_delay: int = Field(
        0,
        description="Number of turns the technique is unavailable at the start of a battle.",
        ge=0,
    )
    starting_charge: int = Field(
        0,
        description="Allows a move to be used multiple times before entering cooldown (if logic supports it).",
        ge=0,
    )
    cooldown_multiplier: float = Field(
        1.0,
        description="A static modifier for how fast this specific tech recharges.",
        ge=0.0,
    )
    range: Range = Field(..., description="The attack range of this technique")
    tech_id: int = Field(..., description="The id of this technique")
    accuracy: float = Field(
        ...,
        description="The accuracy of the technique",
        ge=sizes.ACCURACY_RANGE[0],
        le=sizes.ACCURACY_RANGE[1],
    )
    potency: float = Field(
        ...,
        description="How potent the technique is",
        ge=sizes.POTENCY_RANGE[0],
        le=sizes.POTENCY_RANGE[1],
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> TechniqueModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(TechniqueModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Technique {slug} not found")

    @classmethod
    def load_cache(cls, db: ModData) -> None:
        """Populate the internal cache if it hasn't been populated yet."""
        if not cls._lookup_cache:
            cls._lookup_cache = {
                tech_name: result
                for tech_name in db.database[cls.table_name]
                if (result := cls.lookup(tech_name, db))
            }

    @classmethod
    def get_cache(cls) -> dict[str, TechniqueModel]:
        """Returns the current cache."""
        return cls._lookup_cache

    @field_validator("use_tech", "use_success", "use_failure")
    def translation_exists(cls, v: str | None) -> str | None:
        if not v or has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_tech(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("types")
    def element_exists(cls, elements: Sequence[str]) -> Sequence[str]:
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


class StatusModel(DataModel, BaseLookupModel):
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
    category: CategoryStatus | None = Field(
        None, description="Category status: positive or negative"
    )
    on_positive_status: ResponseStatus | None = Field(
        None,
        description="Determines the response when a positive status is applied",
    )
    on_negative_status: ResponseStatus | None = Field(
        None,
        description="Determines the response when a negative status is applied",
    )
    on_tech_use: str | None = Field(
        None,
        description="Status applied after using a technique",
    )
    on_item_use: str | None = Field(
        None,
        description="Status applied after using an item",
    )
    gain_cond: str | None = Field(
        None,
        description="Slug of what string to display when status is gained",
    )
    use_success: str | None = Field(
        None,
        description="Slug of what string to display when status succeeds",
    )
    use_failure: str | None = Field(
        None,
        description="Slug of what string to display when status fails",
    )
    cond_id: int = Field(..., description="The id of this status")
    stat_modifiers: dict[str, StatModel] = Field(
        default_factory=dict,
        description="Dictionary of stat modifiers keyed by stat name (e.g., 'speed', 'hp')",
    )
    max_stacks: int = Field(
        5, description="Maximum number of stacks this status can accumulate"
    )

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> StatusModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(StatusModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Status {slug} not found")

    @field_validator("icon")
    def file_exists(cls, v: str) -> str:
        if has.file(v) and has.size(v, sizes.STATUS_ICON_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")

    @field_validator("gain_cond", "use_success", "use_failure")
    def translation_exists(cls, v: str | None) -> str | None:
        if not v or has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def translation_exists_cond(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("on_tech_use", "on_item_use")
    def status_exists(cls, v: str | None) -> str | None:
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
    variables: Sequence[GameCondition] = Field(
        default_factory=list,
        description="Sequence of variables that affect the presence of the monster.",
        min_length=1,
    )

    @field_validator("slug")
    def monster_exists(cls, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")


class BagItemModel(BaseModel):
    slug: str = Field(..., description="Slug of the item")
    quantity: int = Field(..., description="Quantity of the item")
    variables: Sequence[GameCondition] = Field(
        default_factory=list,
        description="List of variables that affect the item.",
        min_length=1,
    )

    @field_validator("slug")
    def item_exists(cls, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"the item {v} doesn't exist in the db")


class TemplateModel(DataModel):
    slug: str = Field(
        ..., description="Slug uniquely identifying the template"
    )

    @field_validator("slug")
    def template_exists(cls, v: str) -> str:
        if has.db_entry("template", v):
            return v
        raise ValueError(f"the template {v} doesn't exist in the db")


class NpcTemplateModel(TemplateModel):
    sprite_name: str = Field(
        ...,
        description="Base filename of the overworld sprite sheet (without extension)",
    )
    frame_width: int = Field(
        16,
        description="Width of a single animation frame in the sheet",
    )
    frame_height: int = Field(
        32,
        description="Height of a single animation frame in the sheet",
    )
    rows: int = Field(
        4,
        description="Number of directional rows (front, left, right, back)",
    )
    columns: int = Field(
        3,
        description="Frames per row (walk1, idle, walk2)",
    )
    is_static_prop: bool = Field(
        False,
        description="If True, this NPC uses a single static sprite instead of a sheet",
    )
    animation_speed: float = Field(
        1.0,
        description="Multiplier for animation playback speed",
    )
    frame_divisor: int = Field(
        3,
        description="How many frames per movement cycle",
    )
    speed_factor: float = Field(
        2.0,
        description="Additional speed scaling for this NPC",
    )
    combat_sheet: str = Field(
        ...,
        description="Filename of the combat sprite sheet (side-by-side, back|front)",
    )
    combat_frame_width: int = 64
    combat_frame_height: int = 64
    combat_rows: int = 1
    combat_columns: int = 2

    @field_validator("sprite_name")
    def validate_sheet_exists(cls, v: str) -> str:
        """
        Validate that either:
        - sprites/<name>.png exists (sheet), OR
        - sprites_obj/<name>.png exists (static prop)
        """
        sheet = f"sprites/{v}.png"
        static_obj = f"sprites_obj/{v}.png"

        if has.file(sheet):
            return v

        if has.file(static_obj):
            return v

        raise ValueError(
            f"Neither sprite sheet '{sheet}' nor static prop '{static_obj}' exists"
        )

    @field_validator("combat_sheet")
    def validate_combat_sheet(cls, v: str) -> str:
        file = f"gfx/sprites/player/{v}.png"
        if has.file(file):
            return v
        raise ValueError(f"Combat sheet '{file}' does not exist")


class DialogueContent(BaseModel):
    greeting: str | list[str] | None = Field(
        None, description="Greeting dialogue"
    )
    idle: str | list[str] | None = Field(None, description="Idle chatter")
    farewell: str | list[str] | None = Field(
        None, description="Dialogue when saying goodbye"
    )
    pre_battle: str | list[str] | None = Field(
        None, description="Dialogue before a battle"
    )
    post_battle_win: str | list[str] | None = Field(
        None, description="Dialogue if NPC wins"
    )
    post_battle_lose: str | list[str] | None = Field(
        None, description="Dialogue if NPC loses"
    )
    post_battle_draw: str | list[str] | None = Field(
        None, description="Dialogue if battle is a draw"
    )

    @field_validator("*")
    def translation_exists(
        cls, v: str | list[str] | None
    ) -> str | list[str] | None:
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
    switch_logic: str | None = Field(
        None,
        description=(
            "Defines how the NPC selects a replacement monster when one faints. "
            "Examples include 'random', 'lv_highest', or 'healthiest'."
        ),
    )


class NpcAudioModel(BaseModel):
    battle_music: BattleMusicModel | None = Field(
        None,
        description="Battle music configuration for the NPC; defaults to empty if not set",
    )


class NpcModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "npc"
    _lookup_cache: ClassVar[dict[str, NpcModel]] = {}
    slug: str = Field(..., description="Slug of the name of the NPC")
    birthdate: tuple[int, int] | None = Field(
        None, description="The NPC's birthday represented as (month, day)."
    )
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

    @classmethod
    def load_cache(cls, db: ModData) -> None:
        """Populate the internal cache if it hasn't been populated yet."""
        if not cls._lookup_cache:
            cls._lookup_cache = {
                npc_slug: result
                for npc_slug in db.database[cls.table_name]
                if (result := cls.lookup(npc_slug, db))
            }

    @classmethod
    def get_cache(cls) -> dict[str, NpcModel]:
        """Returns the current cache."""
        return cls._lookup_cache


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

    tray_center_offset: int = Field(
        13, description="Horizontal offset for the tray center point"
    )
    icon_spacing_offset: int = Field(
        8, description="Spacing offset between party icons"
    )
    animation_duration: float = Field(
        2.0, description="Duration of the tray slide-in animation"
    )
    animation_delay: float = Field(
        1.5, description="Delay before the tray starts sliding"
    )
    # Bars
    hp_bar_width: int = Field(
        70, ge=1, description="Default width (scaled units) of the HP bar."
    )
    hp_bar_height: int = Field(
        8, ge=1, description="Default height (scaled units) of the HP bar."
    )
    hp_player_top: int = Field(
        18,
        description="Vertical offset from the top of the player's HUD sprite to place the HP bar.",
    )
    hp_opponent_top: int = Field(
        12,
        description="Vertical offset from the top of the opponent's HUD sprite to place the HP bar.",
    )
    exp_bar_height: int = Field(
        6, ge=1, description="Default height (scaled units) of the EXP bar."
    )
    exp_bar_top: int = Field(
        31,
        description="Vertical offset from the top of the player's HUD sprite to place the EXP bar.",
    )
    bar_right_padding: int = Field(
        8,
        description="Horizontal padding between the right edge of the HUD sprite and the bar's right edge.",
    )

    @field_validator(
        "hud_player",
        "hud_opponent",
        "tray_player",
        "tray_opponent",
    )
    def file_exists(cls, v: str) -> str:
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
    def file_exists(cls, v: str) -> str:
        if has.file(v) and has.size(v, sizes.ICON_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {v}")


class BattleGraphicsModel(BaseModel):
    menu: str = Field(
        "MainCombatMenuState", description="Menu used for combat."
    )
    island_sheet: str = Field(
        ..., description="Sprite sheet containing back+front islands"
    )
    island_width: int = Field(
        96,
        description=(
            "Width of a single island frame inside the island sheet. "
            "The sheet contains two frames arranged horizontally."
        ),
    )
    island_height: int = Field(
        57,
        description=(
            "Height of a single island frame inside the island sheet. "
            "Both frames must share this height."
        ),
    )
    background: str = Field(..., description="Sprite used for background")
    hud: BattleHudModel
    icons: BattleIconsModel
    island_offset_y: int = Field(
        50, description="Vertical shift for islands relative to HUD home"
    )
    enemy_base_offset: int = Field(
        12, description="Vertical offset for enemy relative to island bottom"
    )
    monster_base_offset: int = Field(
        24,
        description="Vertical offset for wild monsters relative to island bottom",
    )
    player_base_offset: int = Field(
        6, description="Vertical offset for player relative to island center"
    )
    entry_jump_distance: int = Field(
        50, description="Vertical 'bounce' during entry."
    )
    entry_duration: float = Field(
        3.0, description="Seconds for the entry transition."
    )
    trainer_exit_offset: int = Field(
        150, description="Pixels to move trainer when leaving"
    )
    trainer_exit_duration: float = Field(
        0.8, description="Duration of trainer exit animation"
    )

    @field_validator("island_sheet")
    def validate_sheet_exists(cls, v: str) -> str:
        if not has.file(v):
            raise ValueError(f"Island sheet not found: {v}")
        return v

    @field_validator("background")
    def background_exists(cls, v: str) -> str:
        if has.file(v) and has.size(v, sizes.BATTLE_BG_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {v}")

    @field_validator("menu")
    def check_state(cls, v: str) -> str:
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


class EnvironmentModel(DataModel, BaseLookupModel):
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
    level_range: tuple[int, int] = Field(
        ...,
        description="Minimum and maximum levels at which this encounter can occur.",
    )
    variables: Sequence[GameCondition] = Field(
        ...,
        description="List of variables that affect the encounter.",
    )
    exp_req_mod: float = Field(
        ...,
        description="Modifier for the experience points required to defeat this wild monster.",
        gt=0.0,
    )
    level_offset: int | None = Field(
        None,
        description="Offset (+/- levels) to apply to the monster's level.",
    )
    level_offset_range: tuple[int, int] | None = Field(
        None,
        description="Range of offset (+/- levels) to apply randomly to base level.",
    )
    min_player_level: int | None = Field(
        None,
        description="Minimum average level of player's party for this encounter.",
    )
    max_player_level: int | None = Field(
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
    scaling_offset_range: tuple[int, int] | None = Field(
        None,
        description="Range used for random offset when scaling level overrides are applied (e.g. [-3, +4])",
    )

    @field_validator("monster")
    def monster_exists(cls, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(f"the monster {v} doesn't exist in the db")

    @field_validator("level_range")
    def validate_level_range(cls, v: tuple[int, int]) -> tuple[int, int]:
        min_allowed, max_allowed = config_monster.level_range
        min_level, max_level = v

        if min_level > max_level:
            raise ValueError("level_range must be (min, max) with min <= max")

        if min_level < min_allowed or max_level > max_allowed:
            raise ValueError(
                f"level_range {v} must be within allowed range "
                f"{config_monster.level_range}"
            )

        return v

    @field_validator("level_offset_range")
    def validate_level_offset_range(
        cls, v: tuple[int, int] | None
    ) -> tuple[int, int] | None:
        if v is None:
            return v

        min_allowed, max_allowed = config_monster.level_range
        off_min, off_max = v

        if off_min > off_max:
            raise ValueError(
                "level_offset_range must be (min, max) with min <= max"
            )

        if off_min < -(max_allowed - min_allowed) or off_max > (
            max_allowed - min_allowed
        ):
            raise ValueError(
                f"level_offset_range {v} would push levels outside allowed range "
                f"{config_monster.level_range}"
            )

        return v

    @field_validator("scaling_offset_range")
    def validate_scaling_offset_range(
        cls, v: tuple[int, int] | None
    ) -> tuple[int, int] | None:
        if v is None:
            return v

        off_min, off_max = v

        if off_min > off_max:
            raise ValueError(
                "scaling_offset_range must be (min, max) with min <= max"
            )

        return v

    @model_validator(mode="after")
    def validate_scaling_logic(self) -> EncounterItemModel:
        """
        Ensures scaling + offsets cannot produce levels outside allowed range.
        """
        min_allowed, max_allowed = config_monster.level_range

        if not self.scaling_enabled:
            return self

        if self.override_level_range:
            if self.scaling_offset_range:
                off_min, off_max = self.scaling_offset_range
                if off_min < -(max_allowed - min_allowed) or off_max > (
                    max_allowed - min_allowed
                ):
                    raise ValueError(
                        f"scaling_offset_range {self.scaling_offset_range} would push "
                        f"scaled levels outside allowed range {config_monster.level_range}"
                    )
            return self

        min_level, max_level = self.level_range
        if min_level < min_allowed or max_level > max_allowed:
            raise ValueError(
                f"scaling cannot use level_range {self.level_range} because it exceeds "
                f"allowed global range {config_monster.level_range}"
            )

        return self


class HordeEncounterModel(BaseModel):
    monsters: Sequence[EncounterItemModel] = Field(
        ..., description="The list of monsters that make up this horde."
    )
    horde_level_range: tuple[int, int] | None = Field(
        None,
        description="Optional: A base level range for the entire horde. "
        "Monsters may have their own level ranges that differ.",
    )
    horde_exp_mod: float | None = Field(
        None,
        description="Optional: A modifier for the experience points of the entire horde.",
        gt=0.0,
    )

    @field_validator("horde_level_range")
    def validate_horde_level_range(
        cls, v: tuple[int, int] | None
    ) -> tuple[int, int] | None:
        if v is None:
            return v

        min_allowed, max_allowed = config_monster.level_range
        min_level, max_level = v

        if min_level > max_level:
            raise ValueError(
                "horde_level_range must be (min, max) with min <= max"
            )

        if min_level < min_allowed or max_level > max_allowed:
            raise ValueError(
                f"horde_level_range {v} must be within allowed range "
                f"{config_monster.level_range}"
            )

        return v


class EncounterType(str, Enum):
    SINGLE = "single"
    HORDE = "horde"


class EncounterModel(DataModel, BaseLookupModel):
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
    horde: HordeEncounterModel | None = Field(
        None, description="Horde data (for horde encounters)"
    )
    scaling_zone: bool = Field(
        False,
        description="If true, this zone applies level scaling to all monsters",
    )
    scale_offset_range: tuple[int, int] | None = Field(
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

    @model_validator(mode="after")
    def validate_encounter_type(self) -> EncounterModel:
        if self.encounter_type == EncounterType.HORDE:
            if not self.horde:
                raise ValueError(
                    "EncounterType.HORDE requires a 'horde' definition"
                )
        else:
            if not self.monsters:
                raise ValueError(
                    "EncounterType.SINGLE requires 'monsters' to be defined"
                )

        return self

    @field_validator("scale_offset_range")
    def validate_scale_offset_range(
        cls, v: tuple[int, int] | None
    ) -> tuple[int, int] | None:
        if v is None:
            return v

        off_min, off_max = v
        if off_min > off_max:
            raise ValueError(
                "scale_offset_range must be (min, max) with min <= max"
            )

        min_allowed, max_allowed = config_monster.level_range
        max_offset = max_allowed - min_allowed

        if off_min < -max_offset or off_max > max_offset:
            raise ValueError(
                f"scale_offset_range {v} would push scaled levels outside allowed range "
                f"{config_monster.level_range}"
            )

        return v

    @model_validator(mode="after")
    def validate_scaling_zone_logic(self) -> EncounterModel:
        min_allowed, max_allowed = config_monster.level_range

        if not self.scaling_zone:
            return self

        if self.override_level_range:
            if self.scale_offset_range:
                off_min, off_max = self.scale_offset_range
                max_offset = max_allowed - min_allowed
                if off_min < -max_offset or off_max > max_offset:
                    raise ValueError(
                        f"scale_offset_range {self.scale_offset_range} would push "
                        f"scaled levels outside allowed range {config_monster.level_range}"
                    )
            return self

        for m in self.monsters:
            min_level, max_level = m.level_range
            if min_level < min_allowed or max_level > max_allowed:
                raise ValueError(
                    f"Monster {m.monster} has level_range {m.level_range} outside "
                    f"global allowed range {config_monster.level_range} while scaling_zone=True"
                )

        return self


class DialogueModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "dialogue"
    _lookup_cache: ClassVar[dict[str, DialogueModel]] = {}
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

    @classmethod
    def load_cache(cls, db: ModData) -> None:
        """Populate the internal cache if it hasn't been populated yet."""
        if not cls._lookup_cache:
            cls._lookup_cache = {
                slug: result
                for slug in db.database[cls.table_name]
                if (result := cls.lookup(slug, db))
            }

    @classmethod
    def get_cache(cls) -> dict[str, DialogueModel]:
        """Returns the current cache."""
        return cls._lookup_cache

    @field_validator("border_slug")
    def file_exists(cls, v: str) -> str:
        file: str = f"gfx/borders/{v}.png"
        if has.file(file) and has.size(file, sizes.BORDERS_SIZE):
            return v
        raise ValueError(f"no resource exists with path: {file}")


class ElementItemModel(BaseModel):
    against: str = Field(..., description="Name of the type")
    multiplier: float = Field(1.0, description="Multiplier against the type")

    @field_validator("against")
    def element_exists(cls, v: str) -> str:
        if not v or has.db_entry("element", v):
            return v
        raise ValueError(f"the element {v} doesn't exist in the db")


class ElementModel(DataModel, BaseLookupModel):
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
    def translation_exists_element(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("slug")
    def sound_call_exists(cls, v: str) -> str:
        if has.db_entry("sounds", f"sound_{v}_call"):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")

    @field_validator("slug")
    def sound_faint_exists(cls, v: str) -> str:
        if has.db_entry("sounds", f"sound_{v}_faint"):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")

    @field_validator("icon")
    def file_exists(cls, v: str) -> str:
        if has.file(v) and has.size(v, sizes.ELEMENT_SIZE):
            return v
        raise ValueError(f"the icon {v} doesn't exist in the db")


class TasteModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "taste"
    _lookup_cache: ClassVar[dict[str, TasteModel]] = {}
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

    @classmethod
    def load_cache(cls, db: ModData) -> None:
        """Populate the internal cache if it hasn't been populated yet."""
        if not cls._lookup_cache:
            cls._lookup_cache = {
                taste_name: result
                for taste_name in db.database[cls.table_name]
                if (result := cls.lookup(taste_name, db)).slug
            }

    @classmethod
    def get_cache(cls) -> dict[str, TasteModel]:
        """Returns the current cache."""
        return cls._lookup_cache

    @field_validator("name")
    def translation_exists_taste(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class EconomyEntityModel(BaseModel):
    """Base class. Do not instantiate directly."""

    price: int = Field(..., description="Price of the entity", ge=0)
    cost: int = Field(..., description="Cost of the entity", ge=0)
    variables: Sequence[GameCondition] = Field(
        default_factory=list,
        description="List of variables that affect the entity in the economy.",
    )


class EconomyItemModel(EconomyEntityModel):
    slug: str = Field(..., description="Slug of the Item")
    inventory: int = Field(
        -1, description="Quantity of the item. -1 means infinite stock."
    )

    @field_validator("slug")
    def item_exists(cls, v: str) -> str:
        if has.db_entry("item", v):
            return v
        raise ValueError(f"Item '{v}' referenced in economy is not in the DB")


class EconomyMonsterModel(EconomyEntityModel):
    slug: str = Field(..., description="Slug of the Monster")
    inventory: int = Field(1, description="Quantity of the monster", gt=0)
    level: int = Field(..., description="Level of the monster", gt=0)

    @field_validator("slug")
    def monster_exists(cls, v: str) -> str:
        if has.db_entry("monster", v):
            return v
        raise ValueError(
            f"Monster '{v}' referenced in economy is not in the DB"
        )


class EconomyModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "economy"
    slug: str = Field(..., description="Slug uniquely identifying the economy")
    resale_multiplier: float = Field(..., description="Resale multiplier")
    background: str = Field(..., description="Sprite used for background")
    items: list[EconomyItemModel]
    monsters: list[EconomyMonsterModel]

    @classmethod
    def lookup(cls, slug: str, db: ModData) -> EconomyModel:
        """Retrieve an instance from the database using a slug."""
        try:
            return cast(EconomyModel, db.lookup(slug, table=cls.table_name))
        except EntryNotFoundError:
            raise RuntimeError(f"Economy {slug} not found")

    @field_validator("background")
    def background_exists(cls, v: str) -> str:
        if not has.file(v):
            raise ValueError(f"Background file not found: {v}")
        if not has.size(v, sizes.NATIVE_RESOLUTION):
            raise ValueError(f"Background file {v} has incorrect resolution")
        return v


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
    variables: Sequence[GameCondition] = Field(
        default_factory=list,
        description="List of variables that affect the requirement.",
        min_length=1,
    )


class RankStep(BaseModel):
    title: str
    threshold: int
    requirement: RankRequirement | None = None


class FactionModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "faction"

    slug: str = Field(..., description="Unique ID of the faction")
    kind: FactionKind | None = Field(
        FactionKind.TEAM, description="Faction type (gym, team, league, etc.)"
    )
    alignment: FactionAlignment | None = Field(
        None, description="Faction alignment: heroic, villainous, rogue, etc."
    )
    badge_id: str | None = Field(
        None, description="Associated badge ID if applicable"
    )
    leader_char: str | None = Field(
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
    def translation_exists_faction(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("members")
    def member_exists(cls, v: Sequence[str]) -> Sequence[str]:
        for npc_slug in v:
            if not has.db_entry("npc", npc_slug):
                raise ValueError(
                    f"The npc '{npc_slug}' doesn't exist in the db"
                )
        return v

    @field_validator("leader_char")
    def leader_exists(cls, v: str | None) -> str | None:
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
    conditions: GameCondition = Field(
        description="Simple conditions on game_variables (all must be true)",
    )
    any_of: list[GameCondition] = Field(
        default_factory=list,
        description="Alternative condition sets; step completes if any are satisfied",
    )
    all_of: list[GameCondition] = Field(
        default_factory=list,
        description="Additional condition sets; all must be satisfied",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Slugs of next steps unlocked when this is completed",
    )
    step_items_needed: dict[str, int | None] = Field(
        default_factory=dict,
        description="Items required to complete this step. Quantity is optional; None means at least one.",
    )
    step_monsters_needed: dict[str, int | None] = Field(
        default_factory=dict,
        description="Monsters required to complete this step. Level is optional; None means any level.",
    )
    optional: bool = Field(False, description="Whether the step is optional")
    auto_complete: bool = Field(
        True,
        description=(
            "If true, the step is automatically marked as completed as soon as its "
            "conditions (conditions, any_of, all_of, item and monster requirements) "
            "are satisfied. If false, the step only becomes unlocked when conditions "
            "are met, but must be completed manually through an explicit game event "
            "such as interacting with an NPC, triggering a script, or performing a "
            "player action."
        ),
    )


class MissionModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "mission"

    slug: str = Field(..., description="Slug uniquely identifying the mission")
    description: str = Field(
        ..., description="Detailed description of the mission objectives"
    )
    prerequisites: Sequence[GameCondition] = Field(
        default_factory=list,
        description="List of game variables required to unlock the mission",
    )
    connected_missions: Sequence[dict[str, Any]] = Field(
        default_factory=list,
        description="List of missions that this one unlocks",
    )
    required_items: dict[str, int | None] = Field(
        default_factory=dict,
        description="Items required to begin the mission with optional quantity. None means at least one.",
    )
    required_monsters: dict[str, int | None] = Field(
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
    failure_conditions: Sequence[GameCondition] = Field(
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
    def translation_exists_mission(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("description")
    def translation_exists_desc(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")

    @field_validator("required_items")
    def item_exists(cls, v: dict[str, int | None]) -> dict[str, int | None]:
        for item_slug in v.keys():
            if not has.db_entry("item", item_slug):
                raise ValueError(
                    f"The item '{item_slug}' doesn't exist in the db"
                )
        return v

    @field_validator("required_monsters")
    def monster_exists(cls, v: dict[str, int | None]) -> dict[str, int | None]:
        for monster_slug in v.keys():
            if not has.db_entry("monster", monster_slug):
                raise ValueError(
                    f"The monster '{monster_slug}' doesn't exist in the db"
                )
        return v


class MusicModel(DataModel):
    slug: str = Field(..., description="Unique slug for the music")
    file: str = Field(..., description="File for the music")

    @field_validator("file")
    def file_exists(cls, v: str) -> str:
        file: str = f"music/{v}"
        if has.file(file):
            return v
        raise ValueError(f"the music {v} doesn't exist in the db")


class SoundModel(DataModel):
    slug: str = Field(..., description="Unique slug for the sound")
    file: str = Field(..., description="File for the sound")

    @field_validator("file")
    def file_exists(cls, v: str) -> str:
        file: str = f"sounds/{v}"
        if has.file(file):
            return v
        raise ValueError(f"the sound {v} doesn't exist in the db")


class AnimationModel(DataModel, BaseLookupModel):
    table_name: ClassVar[str] = "animation"
    slug: str = Field(..., description="Unique slug for the animation")
    file: str = Field(..., description="File of the animation")
    frame_x: int = Field(..., description="Width of each frame in the sheet")
    frame_y: int = Field(..., description="Height of each frame in the sheet")
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
    def file_exists(cls, v: str, info: ValidationInfo) -> str:
        slug = info.data.get("slug")
        sheet_path = f"animations/{v}/{slug}.png"

        if has.file(sheet_path):
            return v

        raise ValueError(f"Animation sheet '{sheet_path}' does not exist")

    @field_validator("duration")
    def validate_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class TerrainModel(DataModel, BaseLookupModel):
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
    def translation_exists_item(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


class WeatherModel(DataModel, BaseLookupModel):
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
    def translation_exists_item(cls, v: str) -> str:
        if has.translation(v):
            return v
        raise ValueError(f"no translation exists with msgid: {v}")


def load_model_map(
    model_map_config: dict[str, str],
) -> dict[str, type[DataModel]]:
    model_map: dict[str, type[DataModel]] = {}
    for table, model_path in model_map_config.items():
        module_name, class_name = model_path.rsplit(".", 1)
        module = import_module(module_name)
        model_map[table] = getattr(module, class_name)
    return model_map
