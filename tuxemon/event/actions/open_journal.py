# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import MonsterModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger()


@final
@dataclass
class OpenJournalAction(EventAction):
    """
    Change to JournalInfoState.

    This action transitions to the JournalInfoState, displaying information
    about a specific monster in the player's journal.

    Script usage:
        .. code-block::

            open_journal <monster_slug>

    Script parameters:
        monster_slug: The slug of the monster to display in the journal.
    """

    name = "open_journal"
    monster_slug: str

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client
        self.action = self.client.event_engine

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name == "JournalInfoState":
            logger.error(
                f"The state 'JournalInfoState' is already active. No action taken."
            )
            return

        journal = MonsterModel.lookup(self.monster_slug, db)
        if journal is None:
            logger.error(
                f"Monster with slug '{self.monster_slug}' not found for JournalInfoState."
            )
            return

        self.client.push_state(
            "JournalInfoState",
            character=self.session.player,
            monster=journal,
            source=self.name,
            reveal=True,
        )

    def update(self, session: Session, dt: float) -> None:
        try:
            session.client.get_state_by_name("JournalInfoState")
        except ValueError:
            self.stop()
