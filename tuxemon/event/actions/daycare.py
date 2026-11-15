# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class DaycareAction(EventAction):
    """
    Withdraw all monsters currently stored in the daycare and return them
    to the specified character's party.

    Script usage:
        .. code-block::

            daycare_withdraw <character>

    Script parameters:
        character: The NPC whose daycare monsters should be withdrawn.
                   This is typically "player", but may refer to any NPC
                   that owns a daycare instance.

    Examples:
        daycare_withdraw player
        daycare_withdraw breeder_npc
    """

    name = "daycare"
    character: str

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        character = self.client.get_npc(self.character)
        if not character:
            self.stop()
            return

        self.client.push_state(
            "DaycareState",
            character=character,
        )

    def update(self, session: Session, dt: float) -> None:
        try:
            session.client.get_state_by_name("DaycareState")
        except ValueError:
            self.stop()
