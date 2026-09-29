# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import KENNEL
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

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
    box: str | None = None

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

        character = session.client.get_monster_owner(monster)
        if character is None:
            logger.error(f"{monster.name}'s owner not found")
            self.stop()
            return

        box = self.box or KENNEL

        if not player.monster_boxes.has_box(box, "monster"):
            logger.error(f"No box found with name {box}")
            self.stop()
            return

        if character.party.transfer_monster_to_box(monster, box):
            logger.info(f"{monster.name} stored in '{box}' box!")
        else:
            logger.error(
                f"Failed to store monster '{monster.name}' in box '{box}'"
            )
