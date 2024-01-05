# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@final
@dataclass
class OverwriteTechAction(EventAction):
    """
    Overwrite / replace a technique with another.

    Script usage:
        .. code-block::

            overwrite_tech <removed>,<added>

    Script parameters:
        removed: Instance id (name variable).
        added: Slug technique.

    eg. "overwrite_tech name_variable,peck"

    """

    name = "overwrite_tech"
    removed: str
    added: str

    def overwrite(self, monster: Monster, removed: Technique) -> None:
        slot = monster.moves.index(removed)
        # creates technique
        added = Technique()
        added.load(self.added)
        # replaces technique
        monster.moves.remove(removed)
        monster.moves.insert(slot, added)
        logger.info(
            f"{monster.name}: {removed.name} replaced by {added.name}!"
        )

    def start(self) -> None:
        player = self.session.player
        # look for the technique
        if self.removed not in player.game_variables:
            logger.error(f"Game variable {self.removed} not found")
            return
        tech_id = uuid.UUID(player.game_variables[self.removed])
        for monster in player.monsters:
            technique = monster.find_tech_by_id(tech_id)
            if technique is None:
                logger.error(f"Technique not found in {monster.name}")
                return
            self.overwrite(monster, technique)
