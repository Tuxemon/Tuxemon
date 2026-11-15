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
class BattleOutcomeCondition(EventCondition):
    """
    Checks if a character has achieved a specific battle outcome
    against an opponent.

    Script usage:
        .. code-block::

            is battle_outcome <fighter>,<outcome>,<opponent>

    Script parameters:
        fighter_slug: The slug of the battle participant (e.g., "player").
        outcome: The desired battle outcome ("won", "lost", or "draw").
        opponent_slug: The slug of the opponent (e.g., "npc_maple").

    Example:
        `is battle_outcome player,won,npc_maple`
        Checks if the 'player' has won against 'npc_maple'.
    """

    name: ClassVar[str] = "battle_outcome"
    fighter: str
    outcome: str
    opponent: str

    def test(self, session: Session) -> bool:

        if self.outcome not in {"won", "lost", "draw"}:
            logger.error(f"Invalid outcome '{self.outcome}'")
            return False

        character = session.client.get_npc(self.fighter)
        if character is None:
            logger.error(f"Character '{self.fighter}' not found")
            return False

        if not character.battle_handler:
            return False
        return character.battle_handler.has_fought_and_outcome(
            outcome=self.outcome, opponent=self.opponent
        )
