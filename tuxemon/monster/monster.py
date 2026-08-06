# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from tuxemon import formula
from tuxemon.database.rules import config_monster
from tuxemon.database.runtime import db
from tuxemon.db import (
    Acquisition,
    EffectPhase,
    EvolutionStage,
    GenderType,
    MonsterModel,
    MonsterSpritesModel,
    StatType,
)
from tuxemon.element import ElementTypesHandler
from tuxemon.fusion import Body
from tuxemon.locale.locale import T
from tuxemon.monster.bond import BondHandler
from tuxemon.monster.evolution import Evolution
from tuxemon.monster.experience import MonsterExperience
from tuxemon.monster.held_item import MonsterItemHandler
from tuxemon.monster.moves import MonsterMovesHandler
from tuxemon.monster.plague import MonsterPlagueHandler
from tuxemon.monster.renderer import SoundConfig, SpriteConfig
from tuxemon.monster.sprite import Flair, FlairApplier
from tuxemon.monster.stats import (
    BasicStats,
    CustomStatBoosts,
    IndividualValues,
    StatCalculator,
    TrainingPoints,
    compare_stats,
    randomize_ivs,
)
from tuxemon.monster.status import MonsterStatusHandler
from tuxemon.platform.const.sizes import MONTH_KEYS
from tuxemon.shape import ShapeHandler
from tuxemon.taste import Taste
from tuxemon.time_handler import random_month_day, today_month_day

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.item.item import Item
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


class Monster:
    """
    Tuxemon monster.

    A class for a Tuxemon monster object. This class acts as a skeleton for
    a Tuxemon, fetching its details from a database.
    """

    _persist_simple = {
        "current_hp": int,
        "name": str,
        "slug": str,
        "birthdate": tuple[int, int] | None,
        "capture_date": tuple[int, int] | None,
        "capture_device": str,
        "height": float,
        "weight": float,
        "taste_cold": str,
        "taste_warm": str,
        "steps": float,
    }

    _persist_include_falsy = {"current_hp", "steps"}

    def __init__(
        self,
        slug: str,
        db_data: MonsterModel,
        instance_id: UUID | None = None,
    ) -> None:
        self.slug: str = slug
        self.instance_id: UUID = instance_id or uuid4()
        self._custom_name: str | None = None

        self.species = db_data.species
        self.stage = db_data.stage
        self.tags = db_data.tags
        self.terrains = db_data.terrains
        self.max_moves = db_data.max_moves
        self.txmn_id = db_data.txmn_id
        self.catch_rate = db_data.catch_rate
        self.upper_catch_resistance = db_data.upper_catch_resistance
        self.lower_catch_resistance = db_data.lower_catch_resistance
        self.gender_weights = db_data.gender_weights

        self.types = ElementTypesHandler(db_data.types)
        self.shape: ShapeHandler = ShapeHandler(db_data.shape)
        self.randomly = db_data.randomly

        self.evolutions = list(db_data.evolutions or [])
        self.history = list(db_data.history or [])
        self.evolution_handler = Evolution(self)

        self._init_assets(db_data)

        self.current_hp: int = 0
        self.steps: float = 0.0
        self.state: str = ""
        self.out_of_range: bool = False
        self.wild: bool = False
        self.waiting_to_evolve: bool = False

        self.is_charging: bool = False
        self.charged_technique: str | None = None
        self.locked_turns_left: int = 0
        self.locked_move: str | None = None
        self.ramp_counter: int = 0
        self.is_confused: bool = False
        self.money_modifier: float = 0.0

        self._levelup_start_stats: BasicStats | None = None
        self._levelup_end_stats: BasicStats | None = None
        self._levelup_start_level: int | None = None
        self._levelup_end_level: int | None = None

        self.acquisition: Acquisition = Acquisition.UNKNOWN
        self.gender = self.assign_gender(self.gender_weights)
        self.owner: NPC | None = None

        self.mother_iid: UUID | None = None
        self.father_iid: UUID | None = None
        self.birthdate: tuple[int, int] | None = None

        self.capture_date: tuple[int, int] | None = None
        self.capture_device: str = "tuxeball"

        self.taste_cold, self.taste_warm = Taste.generate(
            "tasteless", "tasteless"
        )

        self.height: float = 0.0
        self.weight: float = 0.0
        self.height = formula.set_height(self, db_data.height)
        self.weight = formula.set_weight(self, db_data.weight)

        self.moves = MonsterMovesHandler()
        self.moves.set_moveset(db_data.moveset or [])

        self.status = MonsterStatusHandler()
        self.plague = MonsterPlagueHandler()
        self.item_handler = MonsterItemHandler()
        self.experience_handler = MonsterExperience()
        self.bond_handler = BondHandler()

        self.base_stats: BasicStats = BasicStats()
        self.training_points = TrainingPoints()
        self.custom_stats = CustomStatBoosts()
        self.individual_values = randomize_ivs()

        self.body = Body()

    def __repr__(self) -> str:
        return (
            f"<Monster {self.slug!r} lv{self.level}"
            f" hp={self.current_hp}/{self.hp}"
            f" id={self.instance_id.hex[:8]}>"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Monster):
            return NotImplemented
        return self.instance_id == other.instance_id

    def __hash__(self) -> int:
        return hash(self.instance_id)

    def _init_assets(self, db_data: MonsterModel) -> None:
        """Store only metadata for assets. No loading, no SpriteLoader."""
        self.flair_slugs = set(db_data.flairs or [])
        self.flairs: dict[str, Flair] = {}

        sprites = db_data.sprites or MonsterSpritesModel(
            sheet=f"gfx/sprites/battle/{self.slug}-sheet",
        )

        self.sprite_config = SpriteConfig(
            slug=self.slug,
            sheet_path=sprites.sheet,
            front_rect=sprites.front_rect,
            back_rect=sprites.back_rect,
            menu1_rect=sprites.menu1_rect,
            menu2_rect=sprites.menu2_rect,
            flair_slugs=self.flair_slugs,
        )

        primary_slug = self.types.primary.slug

        self.sound_config = SoundConfig(
            combat=db_data.sounds.combat_call if db_data.sounds else None,
            faint=db_data.sounds.faint_call if db_data.sounds else None,
            default_combat=f"sound_{primary_slug}_call",
            default_faint=f"sound_{primary_slug}_faint",
        )

    @classmethod
    def spawn_base(cls, slug: str, level: int) -> Monster:
        """Creates a fresh monster at a given level with initialized stats."""
        db_data = MonsterModel.lookup(slug, db)
        monster = cls(slug, db_data)
        monster.capture_date = today_month_day()
        monster.birthdate = random_month_day()
        monster.experience_handler.set_level(level)
        monster.moves.set_moves(monster)
        monster.set_stats()
        monster.current_hp = monster.hp
        return monster

    @classmethod
    def from_save(cls, save_data: Mapping[str, Any]) -> Monster:
        """Reconstructs a monster from saved state."""
        slug = save_data["slug"]
        db_data = MonsterModel.lookup(slug, db)

        iid = (
            UUID(save_data["instance_id"])
            if "instance_id" in save_data
            else None
        )
        monster = cls(slug, db_data, iid)

        monster.moves.decode_moves(save_data)
        monster.status.decode_status(save_data, monster)
        monster.plague.decode_plagues(save_data)
        monster.bond_handler.set_state(save_data)
        monster.experience_handler = MonsterExperience.from_state(save_data)

        for key, value in save_data.items():
            if key == "body" and value:
                monster.body.set_state(value)
            elif key == "gender" and value:
                monster.gender = GenderType(value)
            elif key == "acquisition" and value:
                monster.acquisition = Acquisition(value)
            elif key == "mother_iid":
                monster.mother_iid = UUID(value) if value else None
            elif key == "father_iid":
                monster.father_iid = UUID(value) if value else None
            elif key in cls._persist_simple:
                setattr(monster, key, value)
            elif key == "held_item" and value:
                item = monster.item_handler.decode_item(value)
                if item:
                    monster.equip_item(item)
            elif key == "training_points" and value:
                monster.training_points = TrainingPoints.from_dict(value)
                monster.training_points.validate()
            elif key == "modifiers" and value:
                monster.custom_stats = CustomStatBoosts.from_dict(value)
            elif key == "individual_values" and value:
                monster.individual_values = IndividualValues.from_dict(value)

        monster.flair_slugs = set(save_data.get("flair_slugs", []))

        if "flairs" in save_data:
            monster.flairs = {
                category: Flair.from_state(flair_data)
                for category, flair_data in save_data["flairs"].items()
            }
        elif monster.flair_slugs:
            monster.flairs = FlairApplier.create(monster.flair_slugs)

        monster.set_stats()

        return monster

    @property
    def name(self) -> str:
        return self._custom_name or T.translate(self.slug)

    @name.setter
    def name(self, value: str) -> None:
        self._custom_name = value

    @property
    def gender_symbol(self) -> str:
        if self.is_male:
            return "\u2642"  # ♂
        if self.is_female:
            return "\u2640"  # ♀
        return ""

    @property
    def is_male(self) -> bool:
        return self.gender is GenderType.MALE

    @property
    def is_female(self) -> bool:
        return self.gender is GenderType.FEMALE

    @property
    def is_genderless(self) -> bool:
        return self.gender is GenderType.NEUTER

    @property
    def description(self) -> str:
        return T.translate(f"{self.slug}_description")

    @property
    def species_name(self) -> str:
        return T.translate(f"cat_{self.species}")

    @property
    def held_item(self) -> Item | None:
        return self.item_handler.held_item

    @property
    def level(self) -> int:
        return self.experience_handler.level

    @property
    def total_experience(self) -> int:
        return self.experience_handler.total_experience

    @property
    def experience_modifier(self) -> float:
        return self.experience_handler.experience_modifier

    @property
    def levelling_up(self) -> bool:
        return self.experience_handler.levelling_up

    @property
    def got_experience(self) -> bool:
        return self.experience_handler.got_experience

    @property
    def experience_progress_percent(self) -> float:
        """Progress toward the next level as a percentage (0.0 to 1.0)."""
        return self.experience_handler.experience_progress_percent

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

    @property
    def birthdate_string(self) -> str:
        if self.birthdate is None:
            return ""

        month, day = self.birthdate

        if 1 <= month <= 12:
            month_name = T.translate(MONTH_KEYS[month - 1])
            return f"{month_name} {day}"

        return ""

    @property
    def capture_string(self) -> str:
        if self.capture_date is None:
            return ""

        month, day = self.capture_date

        if 1 <= month <= 12:
            month_name = T.translate(MONTH_KEYS[month - 1])
            return f"{month_name} {day}"

        return ""

    @property
    def acquisition_string(self) -> str:
        return T.format(
            f"tuxepedia_acquisition_{self.acquisition.value}",
            {"doc": self.capture_string},
        )

    def get_owner(self) -> NPC:
        """Returns the character associated with this monster."""
        if not self.owner:
            raise ValueError("No character is linked to this monster.")
        return self.owner

    def set_owner(self, character: NPC | None) -> None:
        """Sets the NPC associated with this monster."""
        self.owner = character

    def set_acquisition(self, acquisition: Acquisition) -> None:
        """Sets the acquisition method of this monster."""
        self.acquisition = Acquisition(acquisition)
        self.bond_handler.set_bond_for_acquisition(acquisition)

    def has_acquisition(self, method: Acquisition) -> bool:
        """Returns True if the monster was acquired via the specified method."""
        return self.acquisition == method

    def equip_item(self, item: Item) -> bool:
        result = self.item_handler.set_item(item)
        if result:
            self.moves.apply_item_techniques(self, item)
            self.status.apply_item_statuses(self, item)
        return result

    def unequip_item(self) -> Item | None:
        item = self.item_handler.take_item()
        if item:
            self.moves.remove_item_techniques(self, item)
            self.status.remove_item_statuses(item)
            return item
        return None

    def swap_items(self, other: Monster) -> None:
        item_a = self.unequip_item()
        item_b = other.unequip_item()

        if item_a:
            other.equip_item(item_a)
        if item_b:
            self.equip_item(item_b)

    def get_experience_multiplier(self) -> float:
        """
        Retrieves the experience multiplier based on this monster's acquisition
        method, reading from the global formula configuration.
        """
        exp_multiplier = 1.0
        experience_multipliers = config_monster.experience_multipliers

        if experience_multipliers:
            method = self.acquisition.value
            exp_multiplier = experience_multipliers.get(method, 1.0)
            logger.debug(
                f"Experience multiplier for {method}: {exp_multiplier}"
            )

        return exp_multiplier

    def return_stat(self, stat: StatType | str) -> int:
        """
        Returns a monster stat (eg. melee, armour, etc.).
        Accepts either a StatType enum or a string.
        """
        if isinstance(stat, str):
            try:
                stat = StatType(stat.lower())
            except ValueError:
                return 0

        return getattr(self, stat.value, 0)

    def has_type(self, type_slug: str) -> bool:
        """
        Returns TRUE if there is the type among the types.
        """
        return self.types.has_type(type_slug)

    def give_experience(self, amount: int = 1) -> int:
        """Adds experience and triggers synchronization if level changes."""
        old_level = self.level
        levels_earned = self.experience_handler.give_experience(amount)

        if levels_earned > 0:
            saved_xp = self.experience_handler.total_experience
            new_level = self.level  # XP handler already updated it
            self.set_level(new_level, old_level)
            # set_level resets total_experience to the level floor; restore the
            # actual accumulated value so the remainder past the new level is kept
            self.experience_handler.set_total_experience(saved_xp)

        return levels_earned

    def give_tps(
        self, stat_name: str, value: int = config_monster.default_tp_gain
    ) -> None:
        """
        Gives TP points to the monster, respecting global and per-stat limits.
        """
        if stat_name not in BasicStats.names():
            raise ValueError(f"Invalid stat name: {stat_name}")

        current_tps = self.training_points.to_dict()
        total_tps = sum(current_tps.values())

        remaining_total = config_monster.max_total_tps - total_tps
        current_stat_val = getattr(self.training_points, stat_name)
        remaining_stat = config_monster.max_tps - current_stat_val

        points_to_add = max(0, min(value, remaining_total, remaining_stat))

        if points_to_add == 0:
            logger.debug(
                f"No TP added to '{stat_name}' — cap reached "
                f"(remaining_total={remaining_total}, remaining_stat={remaining_stat})."
            )
            return

        new_val = current_stat_val + points_to_add
        self.training_points.set_stat(stat_name, new_val)
        self.training_points.validate()
        logger.debug(
            f"Added {points_to_add} TP to '{stat_name}'. New total: {new_val}"
        )
        self.set_stats()

    def evolution_rank(self) -> int:
        stage_order = {
            EvolutionStage.STAGE2: 4,
            EvolutionStage.STAGE1: 3,
            EvolutionStage.STANDALONE: 2,
            EvolutionStage.BASIC: 1,
        }
        return stage_order.get(self.stage, 0)

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
            custom_stats=self.custom_stats,
            training_points=self.training_points,
            individual_values=self.individual_values,
        )
        self.base_stats = calculator.calculate()

    def get_combat_stats(self) -> BasicStats:
        """Calculates effective stats for the current combat turn."""
        combined_temporary_boosts = BasicStats()

        for status in self.status.get_statuses():
            combined_temporary_boosts += status.temporary_stat_boosts

        held_item = self.item_handler.held_item
        if held_item:
            combined_temporary_boosts += held_item.temporary_stat_boosts

        for move in self.moves.get_moves():
            combined_temporary_boosts += move.temporary_stat_boosts

        calculator = StatCalculator(
            base_stats=self.base_stats,
            level=self.level,
            shape=self.shape,
            taste_cold=self.taste_cold,
            taste_warm=self.taste_warm,
            custom_stats=self.custom_stats,
            training_points=self.training_points,
            individual_values=self.individual_values,
        )

        return calculator.calculate(temporary_boosts=combined_temporary_boosts)

    def clear_all_temporary_boosts(self) -> None:
        for status in self.status.get_statuses():
            status.temporary_stat_boosts = BasicStats()
        for move in self.moves.get_moves():
            move.temporary_stat_boosts = BasicStats()
        if self.item_handler.held_item:
            self.item_handler.held_item.temporary_stat_boosts = BasicStats()

    def set_level(self, new_level: int, old_level: int) -> int:
        if new_level > old_level and self._levelup_start_stats is None:
            self._levelup_start_stats = self.base_stats.copy()
            self._levelup_start_level = old_level

        self.experience_handler.set_level(new_level)
        old_max_hp = self.hp
        self.set_stats()

        if new_level > old_level:
            self._levelup_end_stats = self.base_stats.copy()
            self._levelup_end_level = new_level
            self.current_hp += self.hp - old_max_hp

        level_delta = new_level - old_level

        if level_delta > 0:
            self.moves.update_moves(self, level_delta)
            slug = self.evolution_handler.get_eligible_evolution_slug()

            if slug:
                self.waiting_to_evolve = True
                logger.debug(f"{self.name} is ready to evolve into {slug}!")
            else:
                logger.debug("No evolution flagged at level-up")

        return level_delta

    def consume_levelup_summary(
        self,
    ) -> tuple[int | None, int | None, dict[str, tuple[int, int, int]]] | None:
        if (
            self._levelup_start_stats is None
            or self._levelup_end_stats is None
        ):
            return None

        diff = compare_stats(
            self._levelup_start_stats, self._levelup_end_stats
        )
        start = self._levelup_start_level
        end = self._levelup_end_level

        self._levelup_start_stats = None
        self._levelup_end_stats = None
        self._levelup_start_level = None
        self._levelup_end_level = None

        return start, end, diff

    def set_experience_modifier(self, modifier: float) -> None:
        """Sets the experience modifier for this monster."""
        self.experience_handler.set_experience_modifier(modifier)

    def set_experience_group_slug(self, slug: str) -> None:
        """Sets the experience group slug for this monster."""
        self.experience_handler.set_exp_group(slug)

    def set_total_experience(self, experience: int) -> None:
        """Sets the total experience for this monster."""
        self.experience_handler.set_total_experience(experience)

    def experience_required(self, level_delta: int = 0) -> int:
        """Gets the experience requirement for the given level."""
        return self.experience_handler.experience_required(level_delta)

    @staticmethod
    def assign_gender(weights: dict[GenderType, float]) -> GenderType:
        """Randomly selects a gender based on weighted probabilities."""
        return random.choices(
            population=list(weights.keys()),
            weights=list(weights.values()),
            k=1,
        )[0]

    def transfer_properties_from(self, old_monster: Monster) -> None:
        """Copies essential state and identity properties from the pre-evolved monster."""
        self.experience_handler.set_level(old_monster.level)
        self.experience_handler.set_total_experience(
            old_monster.experience_handler.total_experience
        )
        self.taste_cold = old_monster.taste_cold
        self.taste_warm = old_monster.taste_warm
        self.set_stats()
        self.current_hp = min(old_monster.current_hp, self.hp)
        self.moves = old_monster.moves
        self.status = old_monster.status
        self.instance_id = old_monster.instance_id
        self.individual_values = old_monster.individual_values
        self.training_points = old_monster.training_points
        self.custom_stats = old_monster.custom_stats

        if old_monster.gender in self.gender_weights:
            self.gender = old_monster.gender
        else:
            self.gender = self.assign_gender(self.gender_weights)
            logger.info(
                f"{self.name} changed gender from {old_monster.gender} to {self.gender} upon evolution."
            )

        self.birthdate = old_monster.birthdate
        self.capture_date = old_monster.capture_date
        self.capture_device = old_monster.capture_device
        self.plague = old_monster.plague
        self.steps = old_monster.steps
        self.bond_handler = old_monster.bond_handler

        min_bond = self.bond_handler.get_effective_min_bond(self.stage)
        if self.bond_handler.bond < min_bond:
            self.bond_handler.bond = min_bond

        if old_monster.name != T.translate(old_monster.slug):
            self.name = old_monster.name

        for flair_category in self.flairs:
            if flair_category in old_monster.flairs:
                self.flairs[flair_category] = old_monster.flairs[
                    flair_category
                ]

    def get_state(self) -> Mapping[str, Any]:
        """Serializes the monster into a save-ready dictionary."""

        save_data: dict[str, Any] = {
            attr: getattr(self, attr)
            for attr, _type in self._persist_simple.items()
            if getattr(self, attr) is not None
            or attr in self._persist_include_falsy
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

        body_state = self.body.get_state()
        if body_state:
            save_data["body"] = body_state

        save_data["status"] = self.status.encode_status()
        save_data["moves"] = self.moves.encode_moves()
        save_data["held_item"] = self.item_handler.encode_item()
        save_data["training_points"] = self.training_points.to_dict()
        save_data["individual_values"] = self.individual_values.to_dict()
        save_data["modifiers"] = self.custom_stats.to_dict()
        save_data["bond_dict"] = self.bond_handler.get_state()
        save_data["flair_slugs"] = list(self.flair_slugs)
        save_data["flairs"] = {
            category: flair.get_state()
            for category, flair in self.flairs.items()
        }

        save_data.update(self.experience_handler.get_state())
        return save_data

    def end_combat(self, session: Session) -> None:
        """
        Ends combat, recharges all moves and heals statuses.
        """
        self.clear_all_temporary_boosts()
        self.types.reset_to_default()
        self.moves.reset_current_stats()
        self.out_of_range = False
        self.moves.full_recharge_moves()

        if not self.status.is_fainted:
            current_status = self.status.current_status
            if (
                current_status
                and not current_status.behaviors.persists_after_combat
            ):
                self.status.clear_status(session)

        if self.is_fainted:
            self.current_hp = 0
            self.status.apply_faint(session, self)
            current = self.status.current_status
            if current:
                current.use(session, EffectPhase.ON_FAINT)


def decode_monsters(
    json_data: Sequence[Mapping[str, Any]] | None,
) -> list[Monster]:
    if not json_data:
        return []
    monsters = [Monster.from_save(mon) for mon in json_data]
    for m in monsters:
        if m.capture_date is None:
            m.capture_date = random_month_day()
        if m.birthdate is None:
            m.birthdate = random_month_day()
    return monsters


def encode_monsters(mons: Sequence[Monster]) -> Sequence[Mapping[str, Any]]:
    return [mon.get_state() for mon in mons]
