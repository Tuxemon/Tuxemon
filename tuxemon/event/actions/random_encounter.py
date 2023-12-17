# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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

        # Don't start a battle if we don't even have monsters in our party yet.
        if not check_battle_legal(player):
            return

        slug = self.encounter_slug
        encounters = db.lookup(slug, table="encounter").monsters

        # Filter monsters based on daytime true / false
        filtered = []
        for ele in encounters:
            if (
                ele.daytime is True
                and player.game_variables["daytime"] == "true"
            ):
                filtered.append(ele)
            elif (
                ele.daytime is False
                and player.game_variables["daytime"] == "false"
            ):
                filtered.append(ele)

        if filtered:
            encounter = _choose_encounter(filtered, self.total_prob)
        else:
            # if no monster is set for nighttime, it loads all
            encounter = _choose_encounter(encounters, self.total_prob)

        # If a random encounter was successfully rolled, look up the monster
        # and start the battle.
        if encounter:
            logger.info("Starting random encounter!")

            # get wild monster level
            level = _get_level(encounter)

            # Lookup the environment
            environment = (
                "grass"
                if "environment" not in player.game_variables
                else player.game_variables["environment"]
            )

            # flash color
            rgb = self.rgb if self.rgb else None

            # starts the battle with wild_encounter
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
    encounters: Sequence[EncounterItemModel],
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
