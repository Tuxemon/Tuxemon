# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.combat import check_battle_legal
from tuxemon.db import EncounterItemModel
from tuxemon.encounter import Encounter, EncounterData
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

        encounter_data = EncounterData(self.encounter_slug)
        self.encounter = Encounter(encounter_data)
        filtered_encounters = self.encounter.get_valid_encounters(player)

        if not filtered_encounters:
            logger.error(
                f"No wild monsters, check 'encounter/{self.encounter_slug}.json'"
            )
            return

        encounter = self.encounter.choose_encounter(
            filtered_encounters, self.total_prob
        )
        if encounter:
            logger.info("Starting random encounter!")
            level = self.encounter.get_level(encounter)
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
