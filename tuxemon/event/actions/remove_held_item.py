# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class RemoveHeldItemAction(EventAction):
    """
    Removes a held item from a specific monster.

    Script usage:
        .. code-block::

            remove_held_item <variable>

    Script parameters:
        variable: Name of the variable where to store the monster id.
    """

    name = "remove_held_item"
    variable: str

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

        item = monster.unequip_item()
        if item:
            logger.info(f"{item.name} has been removed from {monster.name}!")
        else:
            logger.error(f"{monster.name} doesn't held an item.")
