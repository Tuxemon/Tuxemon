# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import (
    ACCURACY_RANGE,
    POTENCY_RANGE,
    POWER_RANGE,
)
from tuxemon.session import Session
from tuxemon.technique.technique import Technique
from tuxemon.tools import get_valid_uuid

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
        variable: Name of the variable where the monster UUID is stored.
        technique: Slug of the technique to add (e.g. "bullet").
        power: Optional float (0.0-3.0). Overrides default power.
        potency: Optional float (0.0-1.0). Overrides default potency.
        accuracy: Optional float (0.0-1.0). Overrides default accuracy.

    Examples:
        "add_tech monster_id,flamethrower"
        "add_tech monster_id,flamethrower,2.5,0.8,0.95"
    """

    name = "add_tech"
    variable: str
    technique: str
    power: float | None = None
    potency: float | None = None
    accuracy: float | None = None

    def start(self, session: Session) -> None:
        player = session.player

        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID

        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            logger.error("Monster not found")
            self.stop()
            return

        tech = Technique.create(self.technique)

        overrides = {
            "power": (self.power, POWER_RANGE),
            "potency": (self.potency, POTENCY_RANGE),
            "accuracy": (self.accuracy, ACCURACY_RANGE),
        }

        for attr, (val, bounds) in overrides.items():
            if val is not None:
                lower, upper = bounds
                if lower <= val <= upper:
                    setattr(tech, attr, val)
                    logger.debug(f"Set {tech.slug}.{attr} = {val}")
                else:
                    raise ValueError(
                        f"{attr} value {val} must be between {lower} and {upper}"
                    )

        if monster.moves.has_move(tech.slug):
            logger.warning(f"{monster.name} already knows {tech.name}")
        else:
            monster.moves.learn(monster, tech, ignore_eligibility=True)
            logger.info(f"{monster.name} learned {tech.name}!")
