# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster.plague import InfectionResult, InoculationResult
from tuxemon.tools import get_valid_uuid, parse_flag

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
    condition: str | None = None
    enforced_check: str | None = None

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

        enforce = parse_flag(self.enforced_check)

        condition = self.condition.strip().lower() if self.condition else None
        if condition is None:
            monster.plague.clear_plagues()
        elif condition == "infected":
            if enforce:
                result_infection = monster.plague.try_infect(
                    monster, self.plague_slug
                )
                if result_infection not in (
                    InfectionResult.INFECTED,
                    InfectionResult.CARRIER,
                ):
                    logger.error(f"Failed to infect {monster.name}")
            else:
                monster.plague.infect(self.plague_slug)
        elif condition == "inoculated":
            if enforce:
                result_inoculation = monster.plague.try_inoculate(
                    monster, self.plague_slug
                )
                if result_inoculation not in (
                    InoculationResult.INOCULATED,
                    InoculationResult.ALREADY_INOCULATED,
                ):
                    logger.error(f"Failed to inoculate {monster.name}")
            else:
                monster.plague.inoculate(self.plague_slug)
        else:
            raise ValueError(
                f"Invalid plague condition '{self.condition}'. Must be 'infected' or 'inoculated'."
            )
