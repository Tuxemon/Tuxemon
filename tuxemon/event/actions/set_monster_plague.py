# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, final
from uuid import UUID

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.tools import parse_flag

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterPlagueAction(EventAction):
    """
    Set a monster's plague to the given condition.

    Script usage:
        .. code-block::

            set_monster_plague <variable>,<plague_slug>,<condition>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        plague_slug: The slug of the plague to target.
        condition: Infected, inoculated, or None (removes the plague from the
            character, indicating a healthy state).
        enforced_check: Optional string flag to enforce eligibility rules.
            Accepts "true", "1", or "yes" (case-insensitive).
            Default is False (eligibility is bypassed).
    """

    name = "set_monster_plague"
    variable: str
    plague_slug: str
    condition: Optional[str] = None
    enforced_check: Optional[str] = None

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

        enforce = parse_flag(self.enforced_check)

        condition = self.condition.strip().lower() if self.condition else None
        if condition is None:
            monster.plague.clear_plagues()
        elif condition == "infected":
            if enforce:
                monster.plague.try_infect(monster, self.plague_slug)
            else:
                monster.plague.infect(self.plague_slug)
        elif condition == "inoculated":
            if enforce:
                monster.plague.try_inoculate(monster, self.plague_slug)
            else:
                monster.plague.inoculate(self.plague_slug)
        else:
            raise ValueError(
                f"Invalid plague condition '{self.condition}'. Must be 'infected' or 'inoculated'."
            )
