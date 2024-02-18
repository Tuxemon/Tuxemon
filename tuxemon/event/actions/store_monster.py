# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL

logger = logging.getLogger(__name__)


@final
@dataclass
class StoreMonsterAction(EventAction):
    """
    Store a monster in a box.

    Save the player's monster with the given instance_id to
    the named storage box, removing it from the player party.

    Script usage:
        .. code-block::

            store_monster <variable>[,box]

    Script parameters:
        variable: Name of the variable where to store the monster id.
        box: An existing box where the monster will be stored.

    """

    name = "store_monster"
    variable: str
    box: Optional[str] = None

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
        character = monster.owner
        if character is None:
            logger.error(f"{monster.name}'s owner not found!")
            return

        box = self.box
        if box is None:
            store = KENNEL
        else:
            if box not in character.monster_boxes.keys():
                logger.error(f"No box found with name {box}")
                return
            else:
                store = box
        logger.info(f"{monster.name} stored in {store} box!")
        character.monster_boxes[store].append(monster)
        character.remove_monster(monster)
        label = f"{self.variable}_steps"
        character.game_variables[label] = int(character.steps)
