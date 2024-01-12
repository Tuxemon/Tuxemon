# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.db import TasteCold, TasteWarm
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class ChangeTasteAction(EventAction):
    """
    Changes tastes monster.

    Script usage:
        .. code-block::

            change_taste <monster_id>,<taste>

    Script parameters:
        monster_id: Id of the monster to store.
        taste: warm or cold

    """

    name = "change_taste"
    iid: str
    taste: str

    def start(self) -> None:
        trainer = self.session.player
        # avoid crash by "return"
        if self.iid not in trainer.game_variables:
            return
        monster_id = uuid.UUID(trainer.game_variables[self.iid])

        monster = trainer.find_monster_by_id(monster_id)
        if monster is None:
            logger.debug(
                "Monster not found in party, searching storage boxes."
            )
            monster = trainer.find_monster_in_storage(monster_id)

        if monster is None:
            logger.error(
                f"Could not find monster with instance id {monster_id}"
            )
            return

        if self.taste == "warm":
            warm = list(TasteWarm)
            warm.remove(TasteWarm.tasteless)
            warm.remove(monster.taste_warm)
            r_warm = random.choice(warm)
            monster.taste_warm = r_warm
            monster.set_stats()
        elif self.taste == "cold":
            cold = list(TasteCold)
            cold.remove(TasteCold.tasteless)
            cold.remove(monster.taste_cold)
            r_cold = random.choice(cold)
            monster.taste_cold = r_cold
            monster.set_stats()
        else:
            raise ValueError(f"{self.taste} must be warm or cold")
