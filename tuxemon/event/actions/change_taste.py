# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.db import TasteCold, TasteWarm
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class ChangeTasteAction(EventAction):
    """
    Changes tastes monster.

    Script usage:
        .. code-block::

            change_taste <variable>,<taste>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        taste: warm or cold

    """

    name = "change_taste"
    variable: str
    taste: str

    def start(self) -> None:
        player = self.session.player
        # avoid crash by "return"
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(player.game_variables[self.variable])
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return

        if self.taste == "warm":
            warm = list(TasteWarm)
            warm.remove(TasteWarm.tasteless)
            warm.remove(monster.taste_warm)
            warmer = random.choice(warm)
            logger.info(f"{monster.name}'s {self.taste} taste is {warmer}!")
            monster.taste_warm = warmer
            monster.set_stats()
        elif self.taste == "cold":
            cold = list(TasteCold)
            cold.remove(TasteCold.tasteless)
            cold.remove(monster.taste_cold)
            colder = random.choice(cold)
            logger.info(f"{monster.name}'s {self.taste} taste is {colder}!")
            monster.taste_cold = colder
            monster.set_stats()
        else:
            raise ValueError(f"{self.taste} must be warm or cold")
