# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import EncounterItemModel, db
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)

encounter_cache: dict[str, Sequence[EncounterItemModel]] = {}


@final
@dataclass
class RandomEncounterAction(EventAction):
    """
    Randomly start an encounter.

    Randomly starts a battle with a monster defined in the "encounter" table
    in the "monster.db" database. The chance that this will start a battle
    depends on the "encounter_rate" specified in the database. The
    "encounter_rate" number is the chance
    walking in to this tile will trigger a battle out of 100.
    "total_prob" is an optional override which scales the probabilities so
    that the sum is equal to "total_prob".

    Script usage:
        .. code-block::

            random_encounter <encounter_slug>[,total_prob][,rgb]

    Script parameters:
        encounter_slug: Slug of the encounter list.
        total_prob: Total sum of the probabilities.
        rgb: color (eg red > 255,0,0 > 255:0:0) - default rgb(255,255,255)

    """

    name = "random_encounter"
    encounter_slug: str
    total_prob: Optional[float] = None
    rgb: Optional[str] = None

    def start(self) -> None:
        player = self.session.player

        if not check_battle_legal(player):
            logger.error("Battle is not legal, won't start")
            return

        slug = self.encounter_slug
        encounters = _get_encounters(slug)

        filtered_encounters = [
            _enc
            for _enc in encounters
            if not _enc.variable
            or player.game_variables.get(_enc.variable.split(":")[0])
            == _enc.variable.split(":")[1]
        ]

        if not filtered_encounters:
            logger.error(f"No wild monsters, check 'encounter/{slug}.json'")
            return

        encounter = _choose_encounter(filtered_encounters, self.total_prob)
        if encounter:
            logger.info("Starting random encounter!")
            level = _get_level(encounter)
            environment = player.game_variables.get("environment", "grass")
            rgb = self.rgb if self.rgb else None
            params = [
                encounter.monster,
                level,
                encounter.exp_req_mod,
                None,
                environment,
                rgb,
            ]
            self.session.client.event_engine.execute_action(
                "wild_encounter", params, True
            )


def _choose_encounter(
    encounters: list[EncounterItemModel],
    total_prob: Optional[float],
) -> Optional[EncounterItemModel]:
    """Choose a random encounter based on encounter rates."""
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


def _get_level(encounter: EncounterItemModel) -> int:
    """Get a random level for the encounter."""
    if len(encounter.level_range) > 1:
        return random.randint(
            encounter.level_range[0], encounter.level_range[1] - 1
        )
    else:
        return encounter.level_range[0]


def _get_encounters(cache_key: str) -> Sequence[EncounterItemModel]:
    if cache_key in encounter_cache:
        return encounter_cache[cache_key]
    else:
        try:
            encounters = db.lookup(cache_key, table="encounter").monsters
            encounter_cache[cache_key] = encounters
            return encounters
        except KeyError:
            raise RuntimeError(f"Encounter {cache_key} not found")
