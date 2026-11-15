# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class BattleOutcomeCountCondition(EventCondition):
    """
    Checks if a character has achieved a specific battle outcome a minimum number of times
    against a specific opponent.

    Script usage:

        .. code-block:: text

           is battle_outcome_count <fighter>,<outcome>,<opponent>,<count>

    Script parameters:

        fighter_slug:
            The slug of the battle participant (e.g., "player").

        outcome:
            The desired battle outcome ("won", "lost", or "draw").

        opponent_slug:
            The slug of the opponent (e.g., "npc_maple").

        count:
            Minimum number of times the outcome must have occurred.

    Example:

        .. code-block:: text

           is battle_outcome_count player,won,npc_maple,2

        Checks if the 'player' has won at least 2 times against 'npc_maple'.
    """

    name: ClassVar[str] = "battle_outcome_count"
    fighter: str
    outcome: str
    opponent: str
    required_count: int

    def test(self, session: Session) -> bool:

        if self.outcome not in {"won", "lost", "draw"}:
            logger.error(f"Invalid outcome '{self.outcome}'")
            return False

        character = session.client.get_npc(self.fighter)
        if character is None or not character.battle_handler:
            logger.error(
                f"Character '{self.fighter}' not found or has no battle handler"
            )
            return False

        actual_count = sum(
            1
            for battle in character.battle_handler.get_battles()
            if battle.fighter == self.fighter
            and battle.opponent == self.opponent
            and battle.outcome.value == self.outcome
        )

        return actual_count >= self.required_count
