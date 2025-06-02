# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon import formula, fusion, graphics, prepare, tools
from tuxemon.db import (
    CategoryStatus,
    EvolutionStage,
    GenderType,
    MonsterEvolutionItemModel,
    MonsterHistoryItemModel,
    MonsterMovesetItemModel,
    MonsterSpritesModel,
    PlagueType,
    ResponseStatus,
    StatType,
    db,
)
from tuxemon.element import Element
from tuxemon.evolution import Evolution
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.shape import Shape
from tuxemon.sprite import Sprite
from tuxemon.status.status import Status, decode_status, encode_status
from tuxemon.taste import Taste
from tuxemon.technique.technique import Technique, decode_moves, encode_moves
from tuxemon.time_handler import today_ordinal

if TYPE_CHECKING:
    from pygame.surface import Surface

    from tuxemon.npc import NPC


logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "current_hp",
    "level",
    "name",
    "slug",
    "total_experience",
    "flairs",
    "gender",
    "capture",
    "capture_device",
    "height",
    "weight",
    "taste_cold",
    "taste_warm",
    "traded",
    "steps",
    "bond",
)


@dataclass
class ModifierStats:
    armour: int = 0
    dodge: int = 0
    hp: int = 0
    melee: int = 0
    ranged: int = 0
    speed: int = 0

    def to_dict(self) -> dict[str, int]:
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> ModifierStats:
        return cls(**data)


# class definition for tuxemon flairs:
class Flair:
    def __init__(self, category: str, name: str) -> None:
        self.category = category
        self.name = name


class Monster:
    """
    Tuxemon monster.

    A class for a Tuxemon monster object. This class acts as a skeleton for
    a Tuxemon, fetching its details from a database.
    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.slug = ""
        self.name = ""
        self.cat = ""
        self.description = ""
        self.instance_id = uuid4()

        self.armour = 0
        self.dodge = 0
        self.melee = 0
        self.ranged = 0
        self.speed = 0
        self.current_hp = 0
        self.hp = 0
        self.level = 0
        self.steps = 0.0
        self.bond = prepare.BOND

        self.modifiers = ModifierStats()

        self.moves: list[Technique] = []
        self.moveset: list[MonsterMovesetItemModel] = []
        self.evolutions: list[MonsterEvolutionItemModel] = []
        self.evolution_handler = Evolution(self)
        self.history: list[MonsterHistoryItemModel] = []
        self.stage = EvolutionStage.standalone
        self.flairs: dict[str, Flair] = {}
        self.owner: Optional[NPC] = None
        self.possible_genders: list[GenderType] = []
        self.held_item = MonsterItemHandler()

        self.money_modifier: float = 0.0
        self.experience_modifier: float = 1.0
        self.total_experience = 0

        self.types: list[Element] = []
        self.default_types: list[Element] = []
        self.shape = ""
        self.randomly = True
        self.out_of_range = False
        self.got_experience = False
        self.levelling_up = False
        self.traded = False
        self.wild = False

        self.status: list[Status] = []
        self.plague: dict[str, PlagueType] = {}
        self.taste_cold: str = "tasteless"
        self.taste_warm: str = "tasteless"

        self.max_moves = prepare.MAX_MOVES
        self.txmn_id = 0
        self.capture = 0
        self.capture_device = "tuxeball"
        self.height = 0.0
        self.weight = 0.0

        # The multiplier for checks when a monster ball is thrown this should be a value between 0-100 meaning that
        # 0 is 0% capture rate and 100 has a very good chance of capture. This numbers are based on the capture system
        # calculations. This was originally inspired by the calculations which can be found at:
        # https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_catch_rate, but has been modified to fit with
        # most people's intuitions.
        self.catch_rate = 100.0

        # The catch_resistance value is calculated during the capture. The upper and lower catch_resistance
        # set the span on which the catch_resistance will be. For more information check capture.py
        self.upper_catch_resistance = 1.0
        self.lower_catch_resistance = 1.0

        # The tuxemon's state is used for various animations, etc. For example
        # a tuxemon's state might be "attacking" or "fainting" so we know when
        # to play the animations for those states.
        self.state = ""

        # A fusion body object that contains the monster's face and body
        # sprites, as well as _color scheme.
        self.body = fusion.Body()

        # Set up our sprites.
        self.sprite_handler = MonsterSpriteHandler(
            slug=self.slug,
            front_path="",
            back_path="",
            menu1_path="",
            menu2_path="",
            flairs=self.flairs,
        )

        self.set_state(save_data)
        self.set_stats()

    @classmethod
    def create(
        cls, slug: str, save_data: Optional[Mapping[str, Any]] = None
    ) -> Monster:
        method = cls(save_data)
        method.load(slug)
        return method

    @property
    def hp_ratio(self) -> float:
        return min(self.current_hp / self.hp if self.hp > 0 else 0.0, 1.0)

    @property
    def missing_hp(self) -> int:
        return max(min(self.hp - self.current_hp, self.hp), 0)

    def load(self, slug: str) -> None:
        """
        Loads and sets this monster's attributes from the monster.db database.

        The monster is looked up in the database by name.

        Parameters:
            slug: Slug to lookup.
        """
        try:
            results = db.lookup(slug, table="monster")
        except KeyError:
            raise RuntimeError(f"Monster {slug} not found")

        self.level = random.randint(2, 5)
        self.slug = results.slug
        self.name = T.translate(results.slug)
        self.description = T.translate(f"{results.slug}_description")
        self.cat = results.category
        self.category = T.translate(f"cat_{self.cat}")
        self.shape = results.shape
        self.stage = results.stage or EvolutionStage.standalone
        self.tags = results.tags
        self.taste_cold = self.set_taste_cold(self.taste_cold)
        self.taste_warm = self.set_taste_warm(self.taste_warm)
        self.steps = self.steps
        self.bond = self.bond

        # types
        self.types = [Element(ele) for ele in results.types]
        self.default_types = self.types[:]

        self.randomly = results.randomly or self.randomly
        self.got_experience = self.got_experience
        self.levelling_up = self.levelling_up
        self.traded = self.traded

        self.txmn_id = results.txmn_id
        self.capture = self.set_capture(self.capture)
        self.capture_device = self.capture_device
        self.height = formula.set_height(self, results.height)
        self.weight = formula.set_weight(self, results.weight)
        self.gender = random.choice(list(results.possible_genders))
        self.catch_rate = results.catch_rate or self.catch_rate
        self.upper_catch_resistance = (
            results.upper_catch_resistance or self.upper_catch_resistance
        )
        self.lower_catch_resistance = (
            results.lower_catch_resistance or self.lower_catch_resistance
        )

        self.moveset.extend(results.moveset or [])
        self.evolutions.extend(results.evolutions or [])
        self.history.extend(results.history or [])

        # Look up the monster's sprite image paths
        sprites = results.sprites or MonsterSpritesModel(
            battle1=f"gfx/sprites/battle/{slug}-front",
            battle2=f"gfx/sprites/battle/{slug}-back",
            menu1=f"gfx/sprites/battle/{slug}-menu01",
            menu2=f"gfx/sprites/battle/{slug}-menu02",
        )
        self.flairs = MonsterSpriteHandler.create_flairs(slug)
        self.sprite_handler = MonsterSpriteHandler(
            slug=slug,
            front_path=self.sprite_handler.get_sprite_path(sprites.battle1),
            back_path=self.sprite_handler.get_sprite_path(sprites.battle2),
            menu1_path=self.sprite_handler.get_sprite_path(sprites.menu1),
            menu2_path=self.sprite_handler.get_sprite_path(sprites.menu2),
            flairs=self.flairs,
        )

        # get sound slugs for this monster, defaulting to a generic type-based sound
        self.combat_call = (
            results.sounds.combat_call
            if results.sounds
            else f"sound_{self.types[0].slug}_call"
        )
        self.faint_call = (
            results.sounds.faint_call
            if results.sounds
            else f"sound_{self.types[0].slug}_faint"
        )

    def load_sprites(self, scale: float = prepare.SCALE) -> None:
        """
        Delegates the task of loading sprites to the sprite handler.

        Parameters:
            scale: The scaling factor to resize the sprite images.
                Defaults to the predefined scale value in 'prepare.SCALE'.
        """
        self.sprite_handler.load_sprites(scale)

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

    def learn(self, technique: Technique) -> None:
        """
        Adds a technique to this tuxemon's moveset.

        Parameters:
            technique: The technique for the monster to learn.
        """

        self.moves.append(technique)

    def reset_types(self) -> None:
        """
        Resets monster types to the default ones.
        """
        self.types = self.default_types

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
        return type_slug in {type_obj.slug for type_obj in self.types}

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

        # Level up worthy monsters
        while self.total_experience >= self.experience_required(1):
            self.level_up()
            levels += 1
        return levels

    def apply_status(self, status: Status) -> None:
        """
        Apply a status to the monster by replacing or removing
        the previous status.

        Parameters:
            status: The status.

        """
        if not self.status:
            self.status.append(status)
            return

        if any(t.slug == status.slug for t in self.status):
            return

        self.status[0].nr_turn = 0
        status.nr_turn = 1

        if self.status[0].category == CategoryStatus.positive:
            if status.repl_pos == ResponseStatus.replaced:
                self.status = [status]
            elif status.repl_pos == ResponseStatus.removed:
                self.status.clear()
        elif self.status[0].category == CategoryStatus.negative:
            if status.repl_neg == ResponseStatus.replaced:
                self.status = [status]
            elif status.repl_pos == ResponseStatus.removed:
                self.status.clear()
        else:
            self.status = [status]

    def calculate_base_stats(self) -> None:
        """
        Calculate the base stats of the monster dynamically.
        """
        shape = Shape(self.shape).attributes
        formula.calculate_base_stats(self, shape)

    def apply_stat_updates(self) -> None:
        """
        Apply updates to the monster's stats.
        """
        taste_cold = Taste.get_taste(self.taste_cold)
        taste_warm = Taste.get_taste(self.taste_warm)
        formula.apply_stat_updates(self, taste_cold, taste_warm)

    def set_stats(self) -> None:
        """
        Set or improve stats.

        Sets the monsters initial stats, or improves stats
        when called during a level up.

        """
        self.calculate_base_stats()
        self.apply_stat_updates()

    def set_taste_cold(self, taste_slug: str = "tasteless") -> str:
        """Sets the cold taste of the monster."""

        if taste_slug == "tasteless":
            cold_tastes = [
                taste.slug
                for taste in Taste.get_all_tastes().values()
                if taste.taste_type == "cold" and taste.slug != "tasteless"
            ]
            if cold_tastes:
                self.taste_cold = random.choice(cold_tastes)
            else:
                self.taste_cold = taste_slug
        else:
            taste = Taste.get_taste(taste_slug)
            if taste is None:
                self.taste_cold = taste_slug
            else:
                self.taste_cold = taste.slug

        return self.taste_cold

    def set_taste_warm(self, taste_slug: str = "tasteless") -> str:
        """Sets the warm taste of the monster."""

        if taste_slug == "tasteless":
            warm_tastes = [
                taste.slug
                for taste in Taste.get_all_tastes().values()
                if taste.taste_type == "warm" and taste.slug != "tasteless"
            ]
            if warm_tastes:
                self.taste_warm = random.choice(warm_tastes)
            else:
                self.taste_warm = taste_slug
        else:
            taste = Taste.get_taste(taste_slug)
            if taste is None:
                self.taste_warm = taste_slug
            else:
                self.taste_warm = taste.slug

        return self.taste_warm

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

    def set_moves(self, level: int) -> None:
        """
        Set monster moves according to the level.

        Parameters:
            level: The level of the monster.

        """
        eligible_moves = [
            move.technique
            for move in self.moveset
            if move.level_learned <= level
        ]
        moves_to_learn = eligible_moves[-prepare.MAX_MOVES :]
        for move in moves_to_learn:
            tech = Technique.create(move)
            self.learn(tech)

    def update_moves(self, levels_earned: int) -> list[Technique]:
        """
        Set monster moves according to the levels increased.
        Excludes the moves already learned.

        Parameters:
            levels_earned: Number of levels earned.

        Returns:
            techniques: list containing the learned techniques

        """
        new_level = self.level - levels_earned
        new_moves = self.moves.copy()
        new_techniques = []
        for move in self.moveset:
            if (
                move.technique not in (m.slug for m in self.moves)
                and new_level < move.level_learned <= self.level
            ):
                technique = Technique.create(move.technique)
                new_moves.append(technique)
                new_techniques.append(technique)

        self.moves = new_moves
        return new_techniques

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

        save_data["instance_id"] = str(self.instance_id.hex)
        save_data["plague"] = self.plague

        body = self.body.get_state()
        if body:
            save_data["body"] = body

        save_data["status"] = encode_status(self.status)
        save_data["moves"] = encode_moves(self.moves)
        save_data["held_item"] = self.held_item.encode_item()
        save_data["modifiers"] = self.modifiers.to_dict()

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

        self.moves = []
        for move in decode_moves(save_data.get("moves")):
            self.moves.append(move)
        self.status = []
        for cond in decode_status(save_data.get("status")):
            self.status.append(cond)

        for key, value in save_data.items():
            if key == "body" and value:
                self.body.set_state(value)
            elif key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)
            elif key == "plague" and value:
                self.plague = value
            elif key == "held_item" and value:
                item = self.held_item.decode_item(value)
                if item:
                    self.held_item.set_item(item)
            elif key == "modifiers" and value:
                self.modifiers.from_dict(value)

        self.load_sprites()

    def faint(self) -> None:
        """
        Kills the monster, sets 0 HP and applies faint status.
        """
        faint = Status.create("faint")
        self.current_hp = 0
        self.status.clear()
        self.apply_status(faint)

    def end_combat(self) -> None:
        """
        Ends combat, recharges all moves and heals statuses.
        """
        self.out_of_range = False
        for move in self.moves:
            move.full_recharge()

        if "faint" in (s.slug for s in self.status):
            self.faint()
        else:
            self.status = []

    def find_tech_by_id(self, instance_id: UUID) -> Optional[Technique]:
        """
        Finds a tech among the monster's moves which has the given id.

        """
        return next(
            (m for m in self.moves if m.instance_id == instance_id), None
        )


class MonsterSpriteHandler:
    """Manages the loading, caching, and retrieval of monster sprites."""

    def __init__(
        self,
        slug: str,
        front_path: str,
        back_path: str,
        menu1_path: str,
        menu2_path: str,
        flairs: dict[str, Flair],
    ):
        self.slug = slug
        self.front_path = front_path
        self.back_path = back_path
        self.menu1_path = menu1_path
        self.menu2_path = menu2_path
        self.flairs = flairs
        self.sprite_cache: dict[str, Surface] = {}
        self.animated_sprite_cache: dict[str, Sprite] = {}

    def get_sprite_path(self, sprite: str) -> str:
        """
        Get a sprite path.

        Paths are set up by convention, so the file extension is unknown.
        This adds the appropriate file extension if the sprite exists,
        and returns a dummy image if it can't be found.

        Returns:
            Path to sprite or placeholder image.
        """
        try:
            path = f"{sprite}.png"
            full_path = tools.transform_resource_filename(path)
            if full_path:
                return full_path
        except OSError:
            pass

        logger.error(f"Could not find monster sprite {sprite}")
        return prepare.MISSING_IMAGE

    def load_sprite(self, path: str, **kwargs: Any) -> Surface:
        """
        Loads the monster's sprite images as Pygame surfaces.

        Returns:
            ``True`` if the sprites are already loaded, ``False`` otherwise.
        """
        if path not in self.sprite_cache:
            self.sprite_cache[path] = graphics.load_sprite(
                path, **kwargs
            ).image
        return self.sprite_cache[path]

    def load_animated_sprite(
        self,
        paths: list[str],
        frame_duration: float,
        scale: float = prepare.SCALE,
    ) -> Sprite:
        """Loads and caches an animated sprite."""
        transformed_paths: list[str] = [
            tools.transform_resource_filename(
                f"{path}" if path.endswith(".png") else f"{path}.png"
            )
            for path in paths
        ]
        logger.debug(f"Transformed paths: {transformed_paths}")

        cache_key = f"{'-'.join(transformed_paths)}:{frame_duration}"

        if cache_key not in self.animated_sprite_cache:
            logger.debug(
                f"Caching animated sprite for paths: {transformed_paths}"
            )
            try:
                sprite = graphics.load_animated_sprite(
                    transformed_paths, frame_duration, scale
                )
                self.animated_sprite_cache[cache_key] = sprite
            except ValueError as e:
                logger.error(f"Failed to load animated sprite: {e}")
                raise

        sprite = self.animated_sprite_cache[cache_key]
        return sprite

    def get_sprite(
        self,
        sprite_type: str,
        frame_duration: float = 0.25,
        scale: float = prepare.SCALE,
        **kwargs: Any,
    ) -> Sprite:
        """Returns a Sprite object, applying flairs if necessary."""
        if sprite_type == "front":
            sprite_path = self.front_path
        elif sprite_type == "back":
            sprite_path = self.back_path
        elif sprite_type == "menu01":
            sprite_path = self.menu1_path
        elif sprite_type == "menu02":
            sprite_path = self.menu2_path
        elif sprite_type == "menu":
            return self.load_animated_sprite(
                [self.menu1_path, self.menu2_path], frame_duration, scale
            )
        else:
            raise ValueError(f"Cannot find sprite for: {sprite_type}")

        if sprite_path is None:
            raise ValueError(f"Sprite path for {sprite_type} is not set")

        image = self.load_sprite(sprite_path, **kwargs)

        if self.flairs:
            image = self.apply_flairs(image, sprite_type, **kwargs)

        sprite = Sprite(image=image)
        return sprite

    def apply_flairs(
        self, image: Surface, sprite_type: str, **kwargs: Any
    ) -> Surface:
        """Applies flairs to the given sprite image."""
        for flair in self.flairs.values():
            flair_path = self.get_sprite_path(
                f"gfx/sprites/battle/{self.slug}-{sprite_type}-{flair.name}"
            )
            if flair_path != prepare.MISSING_IMAGE:
                flair_surface = self.load_sprite(flair_path, **kwargs)
                image.blit(flair_surface, (0, 0))
        return image

    def load_sprites(self, scale: float = prepare.SCALE) -> dict[str, Surface]:
        """Loads all monster sprites and caches them."""
        sprite_paths = {
            "front": self.front_path,
            "back": self.back_path,
            "menu01": self.menu1_path,
            "menu02": self.menu2_path,
        }

        return {
            key: graphics.load_and_scale(path, scale)
            for key, path in sprite_paths.items()
        }

    @staticmethod
    def create_flairs(slug: str) -> dict[str, Flair]:
        """Creates the flairs for a given monster slug."""
        if not slug:
            return {}

        results = db.lookup(slug, table="monster")
        flairs: dict[str, Flair] = {}

        for flair in results.flairs:
            if flair.names:
                new_flair = Flair(category=flair.category, name=flair.names[0])
                flairs[new_flair.category] = new_flair

        return flairs


class MonsterItemHandler:
    def __init__(self, item: Optional[Item] = None):
        self.item = item

    def set_item(self, item: Item) -> None:
        if item.behaviors.holdable:
            self.item = item
        else:
            logger.error(f"{item.name} can't be held")

    def get_item(self) -> Optional[Item]:
        return self.item

    def has_item(self) -> bool:
        return self.item is not None

    def clear_item(self) -> None:
        self.item = None

    def encode_item(self) -> Mapping[str, Any]:
        return self.item.get_state() if self.item is not None else {}

    def decode_item(
        self, json_data: Optional[Mapping[str, Any]]
    ) -> Optional[Item]:
        return Item(save_data=json_data) if json_data is not None else None


def decode_monsters(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Monster]:
    return [Monster(save_data=mon) for mon in json_data or {}]


def encode_monsters(mons: Sequence[Monster]) -> Sequence[Mapping[str, Any]]:
    return [mon.get_state() for mon in mons]
