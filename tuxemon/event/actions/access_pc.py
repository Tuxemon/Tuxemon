# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.pc import PCMenuBuilder

logger = logging.getLogger()


@final
@dataclass
class AccessPCAction(EventAction):
    """
    Change to PCState.

    This action transitions to the PCState, typically used for viewing
    player character details or an NPC as if it were a PC.

    Script usage:
        .. code-block::

            access_pc <character_slug>

    Script parameters:
        character_slug: The slug of the character (NPC) to view in PCState.
    """

    name = "access_pc"
    character_slug: str

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name == "PCState":
            logger.error(
                f"The state 'PCState' is already active. No action taken."
            )
            return

        character = get_npc(self.session, self.character_slug)
        if character is None:
            logger.error(
                f"Character '{self.character_slug}' not found for PCState."
            )
            return

        menu_builder = PCMenuBuilder(
            client=self.client, character=character, menu_providers=None
        )
        self.client.push_state(
            "PCState", character=character, menu_builder=menu_builder
        )

    def update(self, session: Session, dt: float) -> None:
        try:
            session.client.get_state_by_name("PCState")
        except ValueError:
            self.stop()
