# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.technique.technique import Technique
from tuxemon.tools import get_valid_uuid

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class OverwriteTechAction(EventAction):
    """
    Replaces a known technique with another for a specific monster.

    This action is typically used when a monster chooses to forget a move
    and learn a new one.

    Script usage:
        .. code-block::

            overwrite_tech <removed>,<added>

    Script parameters:
        removed: Name of the game variable that stores the UUID of the
            technique to be replaced.
        added: Slug of the technique to be added (e.g., "peck", "fireball")

    Example:
        "overwrite_tech name_variable,peck"
    """

    name = "overwrite_tech"
    removed: str
    added: str

    def overwrite(self, monster: Monster, removed: Technique) -> None:
        try:
            slot = monster.moves.current_moves.index(removed)
        except ValueError:
            logger.error(
                f"{removed.slug} not found in current moves of {monster.name}"
            )
            self.stop()
            return

        if monster.moves.has_move(self.added):
            logger.warning(
                f"{monster.name} already knows {self.added}. Overwrite skipped."
            )
            self.stop()
            return

        added_tech = Technique.create(self.added)
        monster.moves.replace_move(slot, added_tech)
        logger.info(
            f"{monster.name} forgot {removed.name} and learned {added_tech.name}"
        )

    def start(self, session: Session) -> None:
        player = session.player
        tech_id = get_valid_uuid(player.game_variables, self.removed)
        if tech_id is None:
            logger.info(
                f"No valid tech selected for variable '{self.removed}'"
            )
            self.stop()
            return  # Exit early if no valid UUID

        for monster in player.monsters:
            technique = monster.moves.find_tech_by_id(tech_id)
            if technique is None:
                logger.error(f"Technique not found in {monster.name}")
                continue

            self.overwrite(monster, technique)
