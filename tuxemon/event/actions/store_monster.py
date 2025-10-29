# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final
from uuid import UUID

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL
from tuxemon.session import Session

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

    def start(self, session: Session) -> None:
        player = session.player

        if not player.game_variables.has(self.variable):
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = UUID(player.game_variables.get(self.variable))
        monster = get_monster_by_iid(session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return

        character = monster.get_owner()
        box = self.box or KENNEL

        if not player.monster_boxes.has_box(box, "monster"):
            logger.error(f"No box found with name {box}")
            return

        success = character.party.transfer_monster_to_box(monster, box)
        if success:
            logger.info(f"{monster.name} stored in '{box}' box!")
        else:
            logger.error(
                f"Failed to store monster '{monster.name}' in box '{box}'"
            )
