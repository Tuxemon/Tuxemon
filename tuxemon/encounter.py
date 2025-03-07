# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon import prepare
from tuxemon.db import EncounterItemModel, db

if TYPE_CHECKING:
    from tuxemon.npc import NPC

logger = logging.getLogger(__name__)


class EncounterData:
    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.encounters = self.load_encounters(slug)

    def load_encounters(self, slug: str) -> Sequence[EncounterItemModel]:
        """Loads encounter data from the db."""
        try:
            results = db.lookup(slug, table="encounter")
        except KeyError:
            raise RuntimeError(f"Encounter {slug} not found")

        return results.monsters

    def get_encounters(self) -> Sequence[EncounterItemModel]:
        """Returns the loaded encounter data."""
        return self.encounters


class Encounter:
    def __init__(self, encounter_data: EncounterData) -> None:
        self.encounter_cache: dict[str, Sequence[EncounterItemModel]] = {}
        self.encounter_data = encounter_data

    def get_valid_encounters(self, character: NPC) -> list[EncounterItemModel]:
        """Returns a list of valid encounters for the given character."""
        if self.encounter_data.slug not in self.encounter_cache:
            encounters = self.encounter_data.get_encounters()
            self.encounter_cache[self.encounter_data.slug] = encounters

        return [
            _enc
            for _enc in self.encounter_cache[self.encounter_data.slug]
            if not _enc.variables
            or all(
                all(
                    character.game_variables.get(key) == value
                    for key, value in variable.items()
                )
                for variable in _enc.variables
            )
        ]

    def choose_encounter(
        self,
        encounters: list[EncounterItemModel],
        total_prob: Optional[float],
    ) -> Optional[EncounterItemModel]:
        """Chooses a random encounter based on encounter rates."""
        if not encounters:
            return None

        total_prob = total_prob or 1.0
        encounter_rate = prepare.CONFIG.encounter_rate_modifier
        scale = float(total_prob) / sum(
            encounter.encounter_rate for encounter in encounters
        )
        scale *= encounter_rate

        total = 0.0
        roll = random.random() * 100
        for encounter in encounters:
            total += encounter.encounter_rate * scale
            if total >= roll:
                return encounter

        return None

    def get_level(self, encounter: EncounterItemModel) -> int:
        """Returns a random level for the encounter."""
        if len(encounter.level_range) > 1:
            return random.randint(
                encounter.level_range[0], encounter.level_range[1] - 1
            )
        else:
            return encounter.level_range[0]
