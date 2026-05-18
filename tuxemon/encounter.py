# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.database.runtime import db
from tuxemon.db import (
    EncounterItemModel,
    EncounterModel,
    EncounterType,
)
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC

logger = logging.getLogger(__name__)

DEFAULT_SCALE_OFFSET = (-2, 2)
ENCOUNTER_ROLL_MAX = 100


@dataclass
class EncounterResult:
    monster: EncounterItemModel
    level: int
    held_item: str | None = None


@dataclass
class HordeEncounterResult:
    monsters: Sequence[EncounterResult]
    horde_exp_mod: float | None = None


class EncounterManager:
    """
    Manages the lifecycle and access to the active encounter zone handler.
    Provides a safe, central API for initiating encounters.
    """

    def __init__(self) -> None:
        self._active_handler: Encounter | None = None
        logger.debug("EncounterManager initialized.")

    def load_zone(self, zone_slug: str) -> bool:
        """
        Loads a new zone by creating an EncounterData and an Encounter object.
        Returns True on success, False on failure.
        """
        self._active_handler = None

        try:
            zone_data = EncounterData(zone_slug)
            self._active_handler = Encounter(zone_data)
            logger.debug(f"Successfully loaded encounter zone: {zone_slug}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to load encounter data for '{zone_slug}': {e}"
            )
            return False

    def unload_zone(self) -> None:
        """Explicitly unloads the current zone, often called when changing maps."""
        self._active_handler = None
        logger.debug("Encounter zone unloaded.")

    def attempt_single_encounter(
        self, character: NPC, total_prob: float
    ) -> EncounterResult | None:
        if self._active_handler:
            return self._active_handler.get_single_encounter(
                character, total_prob
            )
        return None

    def attempt_horde_encounter(
        self, character: NPC, total_prob: float | None = None
    ) -> HordeEncounterResult | None:
        if self._active_handler:
            return self._active_handler.get_horde_encounter(
                character, total_prob
            )
        return None


class EncounterData:
    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.encounter_model = EncounterModel.lookup(slug, db)
        self.encounter_type = self.encounter_model.encounter_type
        self.encounters = self.encounter_model.monsters
        self.horde = self.encounter_model.horde
        self.scaling_zone = self.encounter_model.scaling_zone
        self.override_level_range = self.encounter_model.override_level_range
        self.scale_offset_range = self.encounter_model.scale_offset_range
        self.scale_multiplier = self.encounter_model.scale_multiplier

    def get_encounters(self) -> Sequence[EncounterItemModel]:
        """Returns the loaded encounter data."""
        return self.encounters


class Encounter:
    def __init__(self, zone: EncounterData) -> None:
        self.zone = zone
        self._cache: list[EncounterItemModel] = list(zone.get_encounters())

    def _is_valid(self, enc: EncounterItemModel, character: NPC) -> bool:
        avg_lvl = character.party.level_average
        if avg_lvl is None:
            return False

        if enc.min_player_level and avg_lvl < enc.min_player_level:
            return False
        if enc.max_player_level and avg_lvl > enc.max_player_level:
            return False

        if enc.variables and not character.variable_manager.check_conditions(
            enc.variables
        ):
            return False

        return True

    def get_single_encounter(
        self, character: NPC, total_prob: float
    ) -> EncounterResult | None:
        if self.zone.encounter_type != EncounterType.SINGLE:
            return None

        valid = [e for e in self._cache if self._is_valid(e, character)]
        if not valid:
            logger.error(f"No valid monsters for zone: {self.zone.slug}")
            return None

        weights = [e.encounter_rate for e in valid]
        sum_weights = sum(weights)
        if sum_weights <= 0:
            return None

        roll = random.uniform(0, ENCOUNTER_ROLL_MAX)
        if roll > total_prob * CONFIG.encounter_rate_modifier:
            return None

        chosen = random.choices(valid, weights=weights, k=1)[0]
        level = self.determine_level(character, chosen)
        item = self.get_held_item(chosen)
        return EncounterResult(monster=chosen, level=level, held_item=item)

    def get_horde_encounter(
        self, character: NPC, total_prob: float | None = None
    ) -> HordeEncounterResult | None:
        """
        Returns a list of monsters for a horde encounter.
        """
        if (
            total_prob is not None
            and random.uniform(0, ENCOUNTER_ROLL_MAX) > total_prob
        ):
            return None

        if self.zone.encounter_type != EncounterType.HORDE:
            return None

        horde_model = self.zone.horde
        if not horde_model or not horde_model.monsters:
            return None

        results = []
        for monster_item in horde_model.monsters:
            if not self._is_valid(monster_item, character):
                continue
            level = self.determine_level(character, monster_item)
            held_item = self.get_held_item(monster_item)
            results.append(EncounterResult(monster_item, level, held_item))

        if not results:
            return None

        return HordeEncounterResult(
            monsters=results,
            horde_exp_mod=horde_model.horde_exp_mod,
        )

    def determine_level(
        self, character: NPC, encounter: EncounterItemModel
    ) -> int:
        """Delegates level math to the LevelScaler utility."""
        avg = character.party.level_average or 1

        if encounter.scaling_enabled or self.zone.scaling_zone:
            return LevelScaler.get_scaled_level(avg, encounter, self.zone)

        return LevelScaler.get_static_level(encounter)

    def get_held_item(self, encounter: EncounterItemModel) -> str | None:
        if not encounter.held_items:
            return None

        weights = [item.probability for item in encounter.held_items]
        if sum(weights) <= 0:
            return None

        chosen_item = random.choices(
            encounter.held_items, weights=weights, k=1
        )[0]
        return chosen_item.item_slug


class LevelScaler:
    @staticmethod
    def get_static_level(encounter: EncounterItemModel) -> int:
        """Standard random level generation within a fixed range."""
        base = (
            random.randint(encounter.level_range[0], encounter.level_range[1])
            if len(encounter.level_range) > 1
            else encounter.level_range[0]
        )
        offset = (
            random.randint(*encounter.level_offset_range)
            if encounter.level_offset_range
            else (encounter.level_offset or 0)
        )
        return max(1, base + offset)

    @staticmethod
    def get_scaled_level(
        avg_level: int, encounter: EncounterItemModel, zone: EncounterData
    ) -> int:
        """Dynamic level generation based on a reference average level."""
        override = zone.override_level_range or encounter.override_level_range

        if (zone.scaling_zone or encounter.scaling_enabled) and override:
            base = int(avg_level * (zone.scale_multiplier or 1.0))
            offset_range = zone.scale_offset_range or DEFAULT_SCALE_OFFSET
            return max(1, base + random.randint(*offset_range))

        offset_range = (
            encounter.scaling_offset_range
            or zone.scale_offset_range
            or DEFAULT_SCALE_OFFSET
        )
        return max(1, avg_level + random.randint(*offset_range))
