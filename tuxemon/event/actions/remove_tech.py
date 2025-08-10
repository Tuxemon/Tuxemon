# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, final
from uuid import UUID

from tuxemon.event.eventaction import EventAction
from tuxemon.tools import parse_flag

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RemoveTechAction(EventAction):
    """
    Remove a specific technique from a specific monster in the party.

    Script usage:
        .. code-block::

            remove_tech <tech_id>[,<force_remove>]

    Script parameters:
        tech_id: Name of the variable where the technique ID is stored.
        force_remove: Optional string flag to override forget rules.
            Accepts "true", "1", or "yes" (case-insensitive).

    Examples:
        "remove_tech name_variable"
        "remove_tech name_variable,true"
        "remove_tech name_variable,1"
    """

    name = "remove_tech"
    tech_id: str
    force_remove: Optional[str] = None

    def start(self, session: Session) -> None:
        player = session.player
        if self.tech_id not in player.game_variables:
            logger.error(f"Game variable {self.tech_id} not found")
            return
        tech_id = UUID(player.game_variables[self.tech_id])

        force_remove = parse_flag(self.force_remove)

        for monster in player.monsters:
            technique = monster.moves.find_tech_by_id(tech_id)
            if technique:
                was_removed = (
                    monster.moves.remove_forced(technique)
                    if force_remove
                    else (
                        monster.moves.forget(technique)
                        if monster.moves.can_forget(technique)
                        else False
                    )
                )

                if was_removed:
                    logger.info(
                        f"{technique.name} {'forcibly ' if force_remove else ''}removed from {monster.name}"
                    )
                else:
                    logger.warning(
                        f"{technique.name} could not be removed from {monster.name} (not forgettable)"
                    )
