# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon import formula, fusion, graphics, prepare, tools
from tuxemon.db import (
    CategoryStatus,
    EvolutionStage,
    GenderType,
    MonsterEvolutionItemModel,
    MonsterHistoryItemModel,
    MonsterMovesetItemModel,
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
from tuxemon.status.status import (
    Status,
    decode_status,
    encode_status,
)
from tuxemon.taste import Taste
from tuxemon.technique.technique import Technique, decode_moves, encode_moves
from tuxemon.time_handler import today_ordinal

if TYPE_CHECKING:
    import pygame

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
    "mod_armour",
    "mod_dodge",
    "mod_melee",
    "mod_ranged",
    "mod_speed",
    "mod_hp",
)


# class definition for tuxemon flairs:
class Flair:
    def __init__(self, category: str, name: str) -> None:
        self.category = category
        self.name = name


# class definition for first active tuxemon to use in combat:
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
        self.instance_id = uuid.uuid4()

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

        # modifier values
        self.mod_armour = 0
        self.mod_dodge = 0
        self.mod_melee = 0
        self.mod_ranged = 0
        self.mod_speed = 0
        self.mod_hp = 0

        self.moves: list[Technique] = []
        self.moveset: list[MonsterMovesetItemModel] = []
        self.evolutions: list[MonsterEvolutionItemModel] = []
        self.evolution_handler = Evolution(self)
        self.history: list[MonsterHistoryItemModel] = []
        self.stage = EvolutionStage.standalone
        self.flairs: dict[str, Flair] = {}
        self.battle_cry = ""
        self.faint_cry = ""
        self.owner: Optional[NPC] = None
        self.possible_genders: list[GenderType] = []
        self.held_item = MonsterItemHandler()

        self.money_modifier = 0
        self.experience_modifier = 1
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
        self.sprites: dict[str, pygame.surface.Surface] = {}
        self.front_battle_sprite = ""
        self.back_battle_sprite = ""
        self.menu_sprite_1 = ""
        self.menu_sprite_2 = ""

        self.set_state(save_data)
        self.set_stats()
        self.set_flairs()

    def load_from_db(self, slug: str) -> None:
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
        self.height = self.set_char_height(results.height)
        self.weight = self.set_char_weight(results.weight)
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
        if results.sprites:
            self.front_battle_sprite = self.get_sprite_path(
                results.sprites.battle1
            )
            self.back_battle_sprite = self.get_sprite_path(
                results.sprites.battle2
            )
            self.menu_sprite_1 = self.get_sprite_path(results.sprites.menu1)
            self.menu_sprite_2 = self.get_sprite_path(results.sprites.menu2)

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

    def learn(
        self,
        technique: Technique,
    ) -> None:
        """
        Adds a technique to this tuxemon's moveset.

        Parameters:
            technique: The technique for the monster to learn.

        Examples:

        >>> bulbatux.learn(Technique())
        >>> bulbatux.moves[0].use(bulbatux, target=tuxmander)

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

    def has_type(self, type_slug: Optional[str]) -> bool:
        """
        Returns TRUE if there is the type among the types.
        """
        return (
            type_slug in [type_obj.slug for type_obj in self.types]
            if type_slug
            else False
        )

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
        Calculate the base stats of the monster.
        """
        level = self.level
        multiplier = level + prepare.COEFF_STATS
        shape = Shape(self.shape).attributes
        self.armour = (shape.armour * multiplier) + self.mod_armour
        self.dodge = (shape.dodge * multiplier) + self.mod_dodge
        self.hp = (shape.hp * multiplier) + self.mod_hp
        self.melee = (shape.melee * multiplier) + self.mod_melee
        self.ranged = (shape.ranged * multiplier) + self.mod_ranged
        self.speed = (shape.speed * multiplier) + self.mod_speed

    def apply_stat_updates(self) -> None:
        """
        Apply updates to the monster's stats.
        """
        taste_cold = Taste.get_taste(self.taste_cold)
        taste_warm = Taste.get_taste(self.taste_warm)
        self.armour = formula.update_stat(
            "armour", self.armour, taste_cold, taste_warm
        )
        self.dodge = formula.update_stat(
            "dodge", self.dodge, taste_cold, taste_warm
        )
        self.melee = formula.update_stat(
            "melee", self.melee, taste_cold, taste_warm
        )
        self.ranged = formula.update_stat(
            "ranged", self.ranged, taste_cold, taste_warm
        )
        self.speed = formula.update_stat(
            "speed", self.speed, taste_cold, taste_warm
        )

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

    def set_char_weight(self, value: float) -> float:
        """
        Set weight for each monster.

        """
        result = value if self.weight == value else formula.set_weight(value)
        return result

    def set_char_height(self, value: float) -> float:
        """
        Set height for each monster.

        """
        result = value if self.height == value else formula.set_height(value)
        return result

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
            tech = Technique()
            tech.load(move)
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
                technique = Technique()
                technique.load(move.technique)
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

    def get_sprite(self, sprite: str, **kwargs: Any) -> Sprite:
        """
        Gets a specific type of sprite for the monster.

        Parameters:
            sprite: Name of the sprite type.
            kwargs: Additional parameters to pass to the loading function.

        Returns:
            The surface of the monster sprite.

        """
        sprite_mapping = {
            "front": self.front_battle_sprite,
            "back": self.back_battle_sprite,
            "menu": None,  # handled separately
        }

        if sprite not in sprite_mapping:
            raise ValueError(f"Cannot find sprite for: {sprite}")

        if sprite == "menu":
            assert (
                not kwargs
            ), "kwargs aren't supported for loading menu sprites"
            surface = graphics.load_animated_sprite(
                [self.menu_sprite_1, self.menu_sprite_2], 0.25
            )
        else:
            sprite_path = sprite_mapping[sprite]
            if sprite_path is None:
                raise ValueError(f"Sprite path for {sprite} is not set")
            surface = graphics.load_sprite(sprite_path, **kwargs)

        # Apply flairs to the monster sprite
        for flair in self.flairs.values():
            flair_path = self.get_sprite_path(
                f"gfx/sprites/battle/{self.slug}-{sprite}-{flair.name}"
            )
            if flair_path != prepare.MISSING_IMAGE:
                flair_sprite = graphics.load_sprite(flair_path, **kwargs)
                surface.image.blit(flair_sprite.image, (0, 0))

        return surface

    def set_flairs(self) -> None:
        """Set flairs of this monster if they were not already configured."""
        if len(self.flairs) > 0 or self.slug == "":
            return

        results = db.lookup(self.slug, table="monster")
        for flair in results.flairs:
            new_flair = Flair(
                flair.category,
                random.choice(flair.names),
            )
            self.flairs[new_flair.category] = new_flair

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
            path = "%s.png" % sprite
            full_path = tools.transform_resource_filename(path)
            if full_path:
                return full_path
        except OSError:
            pass

        logger.error(f"Could not find monster sprite {sprite}")
        return prepare.MISSING_IMAGE

    def load_sprites(self) -> bool:
        """
        Loads the monster's sprite images as Pygame surfaces.

        Returns:
            ``True`` if the sprites are already loaded, ``False`` otherwise.

        """
        if self.sprites:
            return True

        sprite_paths = {
            "front": self.front_battle_sprite,
            "back": self.back_battle_sprite,
            "menu": self.menu_sprite_1,
        }

        self.sprites = {
            key: graphics.load_and_scale(path)
            for key, path in sprite_paths.items()
        }
        return False

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

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        Parameters:
            save_data: Data used to reconstruct the monster.

        """
        if not save_data:
            return

        self.load_from_db(save_data["slug"])

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
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)
            elif key == "plague" and value:
                self.plague = value
            elif key == "held_item" and value:
                item = self.held_item.decode_item(value)
                if item:
                    self.held_item.set_item(item)

        self.load_sprites()

    def faint(self) -> None:
        """
        Kills the monster, sets 0 HP and applies faint status.
        """
        faint = Status()
        faint.load("faint")
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

    def find_tech_by_id(self, instance_id: uuid.UUID) -> Optional[Technique]:
        """
        Finds a tech among the monster's moves which has the given id.

        """
        return next(
            (m for m in self.moves if m.instance_id == instance_id), None
        )


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
