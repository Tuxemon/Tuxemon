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
class RemoveFlairAction(EventAction):
    """
    Remove a flair from a monster.

    Script usage:
        .. code-block::

            remove_flair <variable>,<category>

    Script parameters:
        variable: The name of the variable that holds the monster's UUID.
        category: The category of the flair to remove. If omitted, all flairs will be removed.
    """

    name = "remove_flair"
    variable: str
    category: str | None = None

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

        category = self.category.strip().lower() if self.category else None

        if category:
            if category in monster.flairs:
                removed_flair = monster.flairs[category]
                del monster.flairs[category]
                monster.flair_slugs.discard(removed_flair.slug)
                logger.info(f"Removed flair {category} from {monster.name}")
            else:
                logger.warning(
                    f"Flair category '{self.category}' not found for {monster.name}"
                )
        else:
            if monster.flairs:
                monster.flairs.clear()
                monster.flair_slugs.clear()
                logger.info(f"Cleared all flairs for {monster.name}")
            else:
                logger.info(f"No flairs to clear for {monster.name}")
