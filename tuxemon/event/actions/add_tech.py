# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@final
@dataclass
class AddTechAction(EventAction):
    """
    Adds a tech to a specific monster.

    Script usage:
        .. code-block::

            add_tech <variable>,<technique>[,power][,potency][,accuracy]

    Script parameters:
        variable: Name of the variable where to store the monster id.
        technique: Slug of the technique (e.g. "bullet").
        power: Power between 0.0 and 3.0
        potency: Potency between 0.0 and 1.0
        accuracy: Accuracy between 0.0 and 1.0

    """

    name = "add_tech"
    variable: str
    technique: str
    power: Optional[float] = None
    potency: Optional[float] = None
    accuracy: Optional[float] = None

    def start(self) -> None:
        player = self.session.player
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(player.game_variables[self.variable])
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return

        tech = Technique()
        tech.load(self.technique)
        if self.power:
            lower, upper = prepare.POWER_RANGE
            if lower <= self.power <= upper:
                tech.power = self.power
            else:
                raise ValueError(
                    f"{self.power} must be between {lower} and {upper}",
                )
        if self.potency:
            lower, upper = prepare.POTENCY_RANGE
            if lower <= self.potency <= upper:
                tech.potency = self.potency
            else:
                raise ValueError(
                    f"{self.potency} must be between {lower} and {upper}",
                )
        if self.accuracy:
            lower, upper = prepare.ACCURACY_RANGE
            if lower <= self.accuracy <= upper:
                tech.accuracy = self.accuracy
            else:
                raise ValueError(
                    f"{self.accuracy} must be between {lower} and {upper}",
                )
        logger.info(f"{monster.name} learned {tech.name}!")
        monster.learn(tech)
