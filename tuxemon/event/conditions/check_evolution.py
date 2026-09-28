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
class CheckEvolutionCondition(EventCondition):
    """
    Check to see the player has at least one tuxemon evolving.
    If yes, it'll save the monster and the evolution inside a list.
    The list will be used by the event action "evolution".

    Script usage:
        .. code-block::

            is check_evolution <character>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").

    eg. "is check_evolution player"
    """

    name: ClassVar[str] = "check_evolution"
    character: str

    def test(self, session: Session) -> bool:
        target_name = self.character
        target_character = session.client.get_npc(target_name)
        if not target_character:
            return False

        return any(m.waiting_to_evolve for m in target_character.monsters)
