# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.combat import check_battle_legal
from tuxemon.db import EncounterItemModel, db
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


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
            logger.warning("battle is not legal, won't start")
            return

        slug = self.encounter_slug
        encounters = db.lookup(slug, table="encounter").monsters
        filtered = list(encounters)

        for meet in encounters:
            if meet.variable:
                part = meet.variable.split(":")
                if player.game_variables[part[0]] != part[1]:
                    filtered.remove(meet)

        if not filtered:
            logger.info(f"no wild monsters, check encounter/{slug}.json")
            return

        encounter = _choose_encounter(filtered, self.total_prob)

        if encounter:
            logger.info("Starting random encounter!")
            level = _get_level(encounter)
            environment = player.game_variables.get("environment", "grass")
            rgb = self.rgb if self.rgb else None
            self.session.client.event_engine.execute_action(
                "wild_encounter",
                [
                    encounter.monster,
                    level,
                    encounter.exp_req_mod,
                    None,
                    environment,
                    rgb,
                ],
                True,
            )


def _choose_encounter(
    encounters: list[EncounterItemModel],
    total_prob: Optional[float],
) -> Optional[EncounterItemModel]:
    total = 0.0
    roll = random.random() * 100
    if total_prob is not None:
        current_total = sum(
            encounter.encounter_rate for encounter in encounters
        )
        scale = float(total_prob) / current_total
    else:
        scale = 1

    scale *= prepare.CONFIG.encounter_rate_modifier

    for encounter in encounters:
        total += encounter.encounter_rate * scale
        if total >= roll:
            return encounter

    return None


def _get_level(encounter: EncounterItemModel) -> int:
    if len(encounter.level_range) > 1:
        level = random.randrange(
            encounter.level_range[0],
            encounter.level_range[1],
        )
    else:
        level = encounter.level_range[0]

    return level
