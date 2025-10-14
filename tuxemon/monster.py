# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Mapping, Sequence
from dataclasses import fields
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon import formula, prepare
from tuxemon.db import (
    Acquisition,
    EffectPhase,
    EvolutionStage,
    GenderType,
    MonsterEvolutionItemModel,
    MonsterHistoryItemModel,
    MonsterModel,
    MonsterSpritesModel,
    StatType,
    db,
)
from tuxemon.element import ElementTypesHandler
from tuxemon.fusion import Body
from tuxemon.locale import T
from tuxemon.monster_dir.bond import BondHandler
from tuxemon.monster_dir.evolution import Evolution
from tuxemon.monster_dir.held_item import MonsterItemHandler
from tuxemon.monster_dir.moves import MonsterMovesHandler
from tuxemon.monster_dir.plague import MonsterPlagueHandler
from tuxemon.monster_dir.sprite import (
    Flair,
    FlairApplier,
    MonsterSpriteHandler,
    SpriteLoader,
)
from tuxemon.monster_dir.stats import (
    BasicStats,
    StatCalculator,
    TemporaryStatBoosts,
    TrainingPoints,
)
from tuxemon.monster_dir.status import MonsterStatusHandler
from tuxemon.shape import ShapeHandler
from tuxemon.sprite import Sprite
from tuxemon.taste import Taste
from tuxemon.time_handler import today_ordinal

if TYPE_CHECKING:
    pass

    from tuxemon.npc import NPC
    from tuxemon.session import Session


logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "current_hp",
    "level",
    "name",
    "slug",
    "total_experience",
    "capture",
    "capture_device",
    "height",
    "weight",
    "taste_cold",
    "taste_warm",
    "steps",
)


class Monster:
    """
    Tuxemon monster.

    A class for a Tuxemon monster object. This class acts as a skeleton for
    a Tuxemon, fetching its details from a database.
    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.slug: str = ""
        self.name: str = ""
        self.species_name: str = ""
        self.description: str = ""
        self.instance_id: UUID = uuid4()

        self.base_stats: BasicStats = BasicStats()
        self.current_hp: int = 0

        self.level: int = 0
        self.steps: float = 0.0
        self.bond_handler: BondHandler = BondHandler(save_data)

        self.modifiers = TemporaryStatBoosts()
        self.training_points = TrainingPoints()

        self.moves = MonsterMovesHandler()
        self.evolutions: list[MonsterEvolutionItemModel] = []
        self.evolution_handler = Evolution(self)
        self.history: list[MonsterHistoryItemModel] = []
        self.stage: EvolutionStage = EvolutionStage.standalone
        self.flair_slugs: set[str] = set()
        self.flairs: dict[str, Flair] = {}
        self.owner: Optional[NPC] = None
        self.gender_weights: dict[GenderType, float] = {}
        self.held_item = MonsterItemHandler()

        self.money_modifier: float = 0.0
        self.experience_modifier: float = 1.0
        self.total_experience: int = 0

        self.types = ElementTypesHandler()
        self.shape: ShapeHandler = ShapeHandler()
        self.randomly: bool = True
        self.out_of_range: bool = False
        self.got_experience: bool = False
        self.levelling_up: bool = False
        self.acquisition: Acquisition = Acquisition.UNKNOWN
        self.wild: bool = False

        self.status = MonsterStatusHandler()
        self.plague = MonsterPlagueHandler()
        self.taste_cold: str = "tasteless"
        self.taste_warm: str = "tasteless"

        self.txmn_id: int = 0
        self.capture: int = 0
        self.capture_device: str = "tuxeball"
        self.height: float = 0.0
        self.weight: float = 0.0

        self.mother_iid: Optional[UUID] = None
        self.father_iid: Optional[UUID] = None

        # The multiplier for checks when a monster ball is thrown this should be a value between 0-100 meaning that
        # 0 is 0% capture rate and 100 has a very good chance of capture. This numbers are based on the capture system
        # calculations. This was originally inspired by the calculations which can be found at:
        # https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_catch_rate, but has been modified to fit with
        # most people's intuitions.
        self.catch_rate: float = 100.0

        # The catch_resistance value is calculated during the capture. The upper and lower catch_resistance
        # set the span on which the catch_resistance will be. For more information check capture.py
        self.upper_catch_resistance: float = 1.0
        self.lower_catch_resistance: float = 1.0

        # The tuxemon's state is used for various animations, etc. For example
        # a tuxemon's state might be "attacking" or "fainting" so we know when
        # to play the animations for those states.
        self.state: str = ""

        # A fusion body object that contains the monster's face and body
        # sprites, as well as _color scheme.
        self.body = Body()

        # Set up our sprites.
        self.sprite_handler = MonsterSpriteHandler()

        self.set_state(save_data)
        self.set_stats()

    @classmethod
    def create(
        cls, slug: str, save_data: Optional[Mapping[str, Any]] = None
    ) -> Monster:
        method = cls(save_data)
        method.load(slug)
        return method

    @classmethod
    def spawn_base(cls, slug: str, level: int) -> Monster:
        monster = cls.create(slug)
        monster.set_level(level)
        monster.moves.set_moves(monster.instance_id, level, monster.stage)
        monster.current_hp = monster.hp
        return monster

    @property
    def armour(self) -> int:
        return self.base_stats.armour

    @property
    def dodge(self) -> int:
        return self.base_stats.dodge

    @property
    def hp(self) -> int:
        return self.base_stats.hp

    @property
    def melee(self) -> int:
        return self.base_stats.melee

    @property
    def ranged(self) -> int:
        return self.base_stats.ranged

    @property
    def speed(self) -> int:
        return self.base_stats.speed

    @property
    def hp_ratio(self) -> float:
        return min(self.current_hp / self.hp if self.hp > 0 else 0.0, 1.0)

    @property
    def missing_hp(self) -> int:
        return max(min(self.hp - self.current_hp, self.hp), 0)

    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    def load(self, slug: str) -> None:
        """
        Loads and sets this monster's attributes from the monster.db database.

        The monster is looked up in the database by name.

        Parameters:
            slug: Slug to lookup.
        """
        results = MonsterModel.lookup(slug, db)
        self.level = random.randint(2, 5)
        self.slug = results.slug
        self.name = T.translate(results.slug)
        self.description = T.translate(f"{results.slug}_description")
        self.species = results.species
        self.species_name = T.translate(f"cat_{self.species}")
        self.shape = ShapeHandler(results.shape)
        self.stage = results.stage
        self.tags = results.tags
        self.terrains = results.terrains
        self.taste_cold, self.taste_warm = Taste.generate(
            self.taste_cold, self.taste_warm
        )

        self.types = ElementTypesHandler(results.types)

        self.randomly = results.randomly

        self.txmn_id = results.txmn_id
        self.set_capture(self.capture)
        self.height = formula.set_height(self, results.height)
        self.weight = formula.set_weight(self, results.weight)
        self.gender_weights = results.gender_weights
        self.gender = self.assign_gender(results.gender_weights)
        self.catch_rate = results.catch_rate
        self.upper_catch_resistance = results.upper_catch_resistance
        self.lower_catch_resistance = results.lower_catch_resistance

        self.moves.set_moveset(results.moveset or [])
        self.evolutions.extend(results.evolutions or [])
        self.history.extend(results.history or [])

        # Look up the monster's sprite image paths
        sprites = results.sprites or MonsterSpritesModel(
            front=f"gfx/sprites/battle/{slug}-front",
            back=f"gfx/sprites/battle/{slug}-back",
            menu1=f"gfx/sprites/battle/{slug}-menu01",
            menu2=f"gfx/sprites/battle/{slug}-menu02",
        )
        self.flair_slugs = results.flairs
        self.flairs = FlairApplier.create(self.flair_slugs)
        loader = SpriteLoader()
        self.sprite_handler = MonsterSpriteHandler(
            slug=slug,
            front_path=loader.resolve_path(sprites.front),
            back_path=loader.resolve_path(sprites.back),
            menu1_path=loader.resolve_path(sprites.menu1),
            menu2_path=loader.resolve_path(sprites.menu2),
            flairs=self.flairs,
        )

        # get sound slugs for this monster, defaulting to a generic type-based sound
        self.combat_call = (
            results.sounds.combat_call
            if results.sounds.combat_call
            else f"sound_{self.types.primary.slug}_call"
        )
        self.faint_call = (
            results.sounds.faint_call
            if results.sounds.faint_call
            else f"sound_{self.types.primary.slug}_faint"
        )

    def load_sprites(self, scale: float = prepare.SCALE) -> None:
        """
        Delegates the task of loading sprites to the sprite handler.

        Parameters:
            scale: The scaling factor to resize the sprite images.
                Defaults to the predefined scale value in 'prepare.SCALE'.
        """
        self.sprite_handler.load_sprites(scale)

    def get_owner(self) -> NPC:
        """Returns the character associated with this monster."""
        if not self.owner:
            raise ValueError("No character is linked to this monster.")
        return self.owner

    def set_owner(self, character: Optional[NPC]) -> None:
        """Sets the NPC associated with this monster."""
        self.owner = character

    def set_acquisition(self, acquisition: Acquisition) -> None:
        """Sets the acquisition method of this monster."""
        self.acquisition = Acquisition(acquisition)

    def has_acquisition(self, method: Acquisition) -> bool:
        """Returns True if the monster was acquired via the specified method."""
        return self.acquisition == method

    def get_sprite(
        self,
        sprite_type: str,
        frame_duration: float = 0.25,
        scale: float = prepare.SCALE,
        **kwargs: Any,
    ) -> Sprite:
        """
        Retrieves a specific sprite via the sprite handler.

        Parameters:
            sprite_type: The type of sprite to retrieve. Valid options are 'front',
                'back', 'menu01', and 'menu02'.
            frame_duration: The duration of each animation frame
                (applicable only for 'menu')
                Defaults to 0.25 seconds.
            scale: A scaling factor applied to resize the sprite during retrieval.
                (applicable only for 'menu')
                Defaults to the `prepare.SCALE` constant.
            **kwargs: Additional arguments to pass to the sprite handler.

        Returns:
            Sprite: The requested sprite object.
        """
        return self.sprite_handler.get_sprite(
            sprite_type, frame_duration, scale, **kwargs
        )

    def return_stat(self, stat: StatType) -> int:
        """
        Returns a monster stat (eg. melee, armour, etc.).

        Parameters:
            stat: The stat for the monster to return.

        Returns:
            value: The stat.

        """
        stat_map: dict[StatType, int] = {
            StatType.armour: self.armour,
            StatType.dodge: self.dodge,
            StatType.hp: self.hp,
            StatType.melee: self.melee,
            StatType.ranged: self.ranged,
            StatType.speed: self.speed,
        }

        return stat_map.get(stat, 0)

    def has_type(self, type_slug: str) -> bool:
        """
        Returns TRUE if there is the type among the types.
        """
        return self.types.has_type(type_slug)

    def give_experience(self, amount: int = 1) -> int:
        """
        Increase experience.

        Gives the Monster a specified amount of experience, and levels
        up the monster if necessary.

        Parameters:
            amount: The amount of experience to add to the monster.

        Returns:
            int: the amount of levels earned.

        Example:

        >>> bulbatux.give_experience(20)
        """
        self.got_experience = True
        levels = 0
        self.total_experience += amount

        # Level up worthy monsters, but stop at max_level
        while (
            self.level < prepare.MAX_LEVEL
            and self.total_experience >= self.experience_required(1)
        ):
            self.level_up()
            levels += 1
        return levels

    def give_tps(
        self, stat_name: str, value: int = prepare.DEFAULT_TP_GAIN
    ) -> None:
        """
        Gives TP points to the monster's TrainingPoints after a battle,
        respecting the per-stat and total TP limits.
        """
        max_tps = prepare.MAX_TPS
        max_total_tps = prepare.MAX_TOTAL_TPS
        total_tps = sum(
            getattr(self.training_points, field.name)
            for field in fields(self.training_points)
        )
        stat_tps = getattr(self.training_points, stat_name)
        logger.debug(
            f"Attempting to give {value} training_points to '{stat_name}'"
        )
        logger.debug(f"Current training_points for '{stat_name}': {stat_tps}")
        logger.debug(f"Current total training_points: {total_tps}")
        logger.debug(
            f"Remaining total training_points: {max_total_tps - total_tps}"
        )
        logger.debug(
            f"Remaining training_points for '{stat_name}': {max_tps - stat_tps}"
        )
        remaining_total_tps = max_total_tps - total_tps
        points_to_add = min(value, remaining_total_tps, max_tps - stat_tps)
        logger.debug(
            f"training_points to be added to '{stat_name}': {points_to_add}"
        )
        new_stat_tps = stat_tps + points_to_add
        setattr(self.training_points, stat_name, new_stat_tps)
        logger.debug(f"New training_points for '{stat_name}': {new_stat_tps}")
        self.set_stats()

    def set_stats(self) -> None:
        """
        Set or improve stats.

        Sets the monsters initial stats, or improves stats
        when called during a level up.
        """
        calculator = StatCalculator(
            base_stats=self.base_stats,
            level=self.level,
            shape=self.shape,
            taste_cold=self.taste_cold,
            taste_warm=self.taste_warm,
            modifiers=self.modifiers,
            training_points=self.training_points,
        )
        self.base_stats = calculator.calculate()

    def set_capture(self, amount: int) -> int:
        """
        It returns the capture date.
        """
        self.capture = today_ordinal() if amount == 0 else amount
        return self.capture

    def level_up(self) -> None:
        """
        Increases a Monster's level by one and increases stats accordingly.

        """
        logger.info(
            f"Leveling {self.name} from {self.level} to {self.level + 1}!"
        )
        # Increase Level and stats
        self.levelling_up = True
        self.level = min(self.level + 1, prepare.MAX_LEVEL)
        self.set_stats()

    def set_level(self, level: int) -> None:
        """
        Set monster level.

        Sets the Monster's level to the specified arbitrary level,
        and modifies experience accordingly.
        Does not let level go above MAX_LEVEL or below 1.

        Parameters:
            level: The level to set the monster to.

        Example:

        >>> bulbatux.set_level(20)

        """
        self.level = min(max(level, 1), prepare.MAX_LEVEL)
        self.total_experience = self.experience_required()
        self.set_stats()

    def experience_required(self, level_ofs: int = 0) -> int:
        """
        Gets the experience requirement for the given level.

        Parameters:
            level_ofs: Difference in levels with the current level.

        Returns:
            Required experience.

        """
        required = (self.level + level_ofs) ** prepare.COEFF_EXP
        return int(required)

    def assign_gender(self, weights: dict[GenderType, float]) -> GenderType:
        """Randomly selects a gender based on weighted probabilities."""
        return random.choices(
            population=list(weights.keys()),
            weights=list(weights.values()),
            k=1,
        )[0]

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the monster to be saved to a file.

        Returns:
            Dictionary containing all the information about the monster.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = self.instance_id.hex
        save_data["gender"] = self.gender
        save_data["acquisition"] = self.acquisition
        save_data["plague"] = self.plague.encode_plagues()
        save_data["mother_iid"] = (
            self.mother_iid.hex if self.mother_iid else None
        )
        save_data["father_iid"] = (
            self.father_iid.hex if self.father_iid else None
        )

        body = self.body.get_state()
        if body:
            save_data["body"] = body

        save_data["status"] = self.status.encode_status()
        save_data["moves"] = self.moves.encode_moves()
        save_data["held_item"] = self.held_item.encode_item()
        save_data["training_points"] = self.training_points.to_dict()
        save_data["modifiers"] = self.modifiers.to_dict()
        save_data["bond_dict"] = self.bond_handler.get_state()
        save_data["flair_slugs"] = list(self.flair_slugs)
        save_data["flairs"] = {
            category: flair.get_state()
            for category, flair in self.flairs.items()
        }

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        Parameters:
            save_data: Data used to reconstruct the monster.

        """
        if not save_data:
            return

        self.load(save_data["slug"])

        self.moves.decode_moves(save_data)
        self.status.decode_status(save_data, self)
        self.plague.decode_plagues(save_data)
        self.bond_handler.set_state(save_data)

        for key, value in save_data.items():
            if key == "body" and value:
                self.body.set_state(value)
            elif key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key == "gender" and value:
                self.gender = GenderType(value)
            elif key == "acquisition" and value:
                self.acquisition = Acquisition(value)
            elif key == "mother_iid":
                self.mother_iid = UUID(value) if value else None
            elif key == "father_iid":
                self.father_iid = UUID(value) if value else None
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)
            elif key == "held_item" and value:
                item = self.held_item.decode_item(value)
                if item:
                    self.held_item.set_item(item)
            elif key == "training_points" and value:
                self.training_points.from_dict(value)
            elif key == "modifiers" and value:
                self.modifiers.from_dict(value)
            elif key == "flairs" and value:
                self.flairs = {
                    category: Flair.from_state(flair_data)
                    for category, flair_data in value.items()
                }
            elif key == "flair_slugs" and value:
                self.flair_slugs = set(value)
                if "flairs" not in save_data:
                    self.flairs = FlairApplier.create(self.flair_slugs)

        self.load_sprites()

    def end_combat(self, session: Session) -> None:
        """
        Ends combat, recharges all moves and heals statuses.
        """
        self.out_of_range = False
        self.moves.full_recharge_moves()

        if not self.status.is_fainted:
            self.status.remove_status()

        if self.is_fainted:
            self.current_hp = 0
            self.status.apply_faint(self)
            current = self.status.get_current_status()
            if current:
                current.use(session, EffectPhase.ON_FAINT)


def decode_monsters(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Monster]:
    return [Monster(save_data=mon) for mon in json_data or {}]


def encode_monsters(mons: Sequence[Monster]) -> Sequence[Mapping[str, Any]]:
    return [mon.get_state() for mon in mons]
