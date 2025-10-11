# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

from tuxemon import prepare
from tuxemon.db import (
    EncounterItemModel,
    EncounterModel,
    EncounterType,
    HordeEncounterModel,
    db,
)

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


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
        self.zone_cache: dict[
            str, Sequence[Union[EncounterItemModel, HordeEncounterModel]]
        ] = {}

    def is_scaling_zone(self) -> bool:
        return self.zone.scaling_zone

    def _get_valid_single_encounters(
        self, character: NPC
    ) -> list[EncounterItemModel]:
        """
        Internal helper to get a list of valid single monster encounters.
        """
        if self.zone.slug not in self.zone_cache:
            self.zone_cache[self.zone.slug] = self.zone.get_encounters()

        player_avg_level = character.party.level_average
        if player_avg_level is None:
            return []

        valid_encs = []
        for _enc in self.zone_cache[self.zone.slug]:
            if not isinstance(_enc, EncounterItemModel):
                continue

            is_valid = True
            if _enc.variables:
                for variable in _enc.variables:
                    for key, value in variable.items():
                        if character.game_variables.get(key) != value:
                            is_valid = False
                            break
                    if not is_valid:
                        break
            if not is_valid:
                continue
            if (
                _enc.min_player_level is not None
                and player_avg_level < _enc.min_player_level
            ):
                continue
            if (
                _enc.max_player_level is not None
                and player_avg_level > _enc.max_player_level
            ):
                continue

            valid_encs.append(_enc)
            logger.debug(f"[Valid] Single monster '{_enc.monster}' is valid")

        if not valid_encs:
            logger.error(
                f"No wild monsters, check 'encounter/{self.zone.slug}.json'"
            )
        return valid_encs

    def _choose_single_encounter(
        self, encounters: list[EncounterItemModel], total_prob: float
    ) -> Optional[EncounterItemModel]:
        """
        Internal helper to choose one single monster based on rates.
        """
        if not encounters:
            return None

        sum_rates = sum(enc.encounter_rate for enc in encounters)
        if sum_rates == 0:
            return None

        encounter_rate_modifier = prepare.CONFIG.encounter_rate_modifier
        scale = (total_prob / sum_rates) * encounter_rate_modifier

        total = 0.0
        roll = random.random() * 100
        for encounter in encounters:
            rate = encounter.encounter_rate * scale
            logger.debug(
                f"[Rate] Monster '{encounter.monster}' weighted rate: {rate:.2f}"
            )
            total += rate
            if total >= roll:
                logger.debug(
                    f"[Chosen] Rolled {roll:.2f}, selected '{encounter.monster}'"
                )
                return encounter
        return None

    def get_single_encounter(
        self, character: NPC, total_prob: float
    ) -> Optional[tuple[EncounterItemModel, int, Optional[str]]]:
        """
        Public method to get a single monster encounter.
        """
        if self.zone.encounter_type != EncounterType.SINGLE:
            return None

        valid_encs = self._get_valid_single_encounters(character)
        chosen_encounter = self._choose_single_encounter(
            valid_encs, total_prob
        )

        if chosen_encounter:
            level = self.determine_level(character, chosen_encounter)
            held_item = self.get_held_item(chosen_encounter)
            return (chosen_encounter, level, held_item)

        return None

    def get_horde_encounter(
        self,
        character: NPC,
    ) -> Optional[list[tuple[EncounterItemModel, int, Optional[str]]]]:
        """
        Public method to get a horde encounter.
        """
        if self.zone.encounter_type != EncounterType.HORDE:
            return None

        horde_model = self.zone.horde
        if not horde_model or not horde_model.monsters:
            return None

        battle_monsters = []
        for monster_in_horde in horde_model.monsters:
            level = self.determine_level(character, monster_in_horde)
            held_item = self.get_held_item(monster_in_horde)
            battle_monsters.append((monster_in_horde, level, held_item))

        return battle_monsters

    def get_level(self, encounter: EncounterItemModel) -> int:
        """Returns a random level for the encounter, applying the level offset."""
        base = (
            random.randint(
                encounter.level_range[0], encounter.level_range[1] - 1
            )
            if len(encounter.level_range) > 1
            else encounter.level_range[0]
        )

        offset = (
            random.randint(*encounter.level_offset_range)
            if encounter.level_offset_range
            else (encounter.level_offset or 0)
        )

        return max(1, base + offset)

    def get_held_item(self, encounter: EncounterItemModel) -> Optional[str]:
        """Returns a random held item for the encounter based on probabilities."""
        if not encounter.held_items:
            logger.debug(
                f"[HeldItem] No held items for monster '{encounter.monster}'"
            )
            return None

        total_prob = sum(item.probability for item in encounter.held_items)
        if total_prob == 0:
            logger.debug(
                f"[HeldItem] Held items exist but total probability is zero for '{encounter.monster}'"
            )
            return None

        roll = random.uniform(0, total_prob)
        logger.debug(
            f"[HeldItem] Rolled {roll:.2f} (range 0-{total_prob:.2f}) for monster '{encounter.monster}'"
        )

        current_prob_sum = 0.0
        for item_data in encounter.held_items:
            current_prob_sum += item_data.probability
            logger.debug(
                f"[HeldItem] Checking item '{item_data.item_slug}' with threshold {current_prob_sum:.2f}"
            )
            if roll <= current_prob_sum:
                logger.debug(
                    f"[HeldItem] Selected item: '{item_data.item_slug}'"
                )
                return item_data.item_slug

        logger.debug(f"[HeldItem] No item selected — fallback to None")
        return None

    def get_scaled_level(
        self, character: NPC, encounter: EncounterItemModel
    ) -> int:
        level_avg = character.party.level_average or 1
        override = (
            self.zone.override_level_range or encounter.override_level_range
        )
        zone = self.zone

        if (self.is_scaling_zone() or encounter.scaling_enabled) and override:
            base = int(level_avg * (zone.scale_multiplier or 1.0))
            if zone.scale_offset_range:
                offset = random.randint(*zone.scale_offset_range)
            else:
                offset = random.randint(-2, +2)
            level = max(1, base + offset)
            logger.debug(
                f"[ScalingOverride] Base: {base}, Offset: {offset}, Final: {level}"
            )
            return level
        else:
            # Standard scaling within level_range
            base_min, base_max = encounter.level_range
            base = max(base_min, min(level_avg, base_max - 1))
            offset_range = (
                encounter.scaling_offset_range
                or self.zone.scale_offset_range
                or (-2, 2)
            )
            offset = random.randint(*offset_range)
            level = max(1, level_avg + offset)
            logger.debug(
                f"[Scaling] Standard scaling — level clamped to range: {level}"
            )
            return level

    def determine_level(
        self, character: NPC, encounter: EncounterItemModel
    ) -> int:
        if encounter.scaling_enabled or self.is_scaling_zone():
            level = self.get_scaled_level(character, encounter)
            logger.debug(
                f"[Scaling] Encounter '{encounter.monster}' scaled to level {level} "
                f"(Party avg: {character.party.level_average})"
            )
        else:
            level = self.get_level(encounter)
            logger.debug(
                f"[Static] Encounter '{encounter.monster}' using static level {level}"
            )
        return level
