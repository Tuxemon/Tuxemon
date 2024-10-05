# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.db import db
from tuxemon.event import get_monster_by_iid, get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster

logger = logging.getLogger()


@final
@dataclass
class ChangeStateAction(EventAction):
    """
    Change to the specified state.

    Script usage:
        .. code-block::

            change_state <state_name>[,optional]

    Script parameters:
        state_name: The state name to switch to (e.g. PCState).
        optional: Variable related to specific states
            (e.g. variable with monster_id for MonsterInfo, monster slug
            for JournalInfoState and character slug for CharacterState).

    """

    name = "change_state"
    state_name: str
    optional: Optional[str] = None

    def start(self) -> None:
        self.client = self.session.client
        self.action = self.client.event_engine

        if self.client.current_state is None:
            raise RuntimeError("Current state is None")

        if self.client.current_state.name == self.state_name:
            return  # No need to change state if already in the target state

        self._handle_state_transition()

    def _handle_state_transition(self) -> None:
        """Handle the state transition based on the target state."""
        if self.state_name == "JournalInfoState" and self.optional:
            self._handle_journal_info_state(self.optional)
        elif self.state_name == "MonsterInfoState" and self.optional:
            self._handle_monster_info_state(self.optional)
        elif self.state_name == "CharacterState" and self.optional:
            self._handle_character_state(self.optional)
        else:
            self.client.push_state(self.state_name)

    def _handle_journal_info_state(self, optional: str) -> None:
        """Handle the JournalInfoState transition."""
        journal = db.lookup(optional, table="monster")
        if journal is None:
            logger.error("Journal not found")
            return

        _set_tuxepedia = ["player", journal.slug, "caught"]
        self.action.execute_action("set_tuxepedia", _set_tuxepedia, True)
        params = {"monster": journal}
        self.client.push_state(self.state_name, kwargs=params)
        self.action.execute_action("clear_tuxepedia", [journal.slug], True)

    def _handle_monster_info_state(self, optional: str) -> None:
        """Handle the MonsterInfoState transition."""
        monster = self.retrieve_monster(optional)
        if monster is None:
            logger.error("Monster not found")
            return

        params = {"monster": monster, "source": self.name}
        self.client.push_state(self.state_name, kwargs=params)

    def _handle_character_state(self, optional: str) -> None:
        """Handle the CharacterState transition."""
        character = get_npc(self.session, optional)
        if character is None:
            logger.error(f"{self.optional} not found")
            return

        params = {"character": character}
        self.client.push_state(self.state_name, kwargs=params)

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(self.state_name)
        except ValueError:
            self.stop()

    def retrieve_monster(self, variable: str) -> Optional[Monster]:
        """Retrieve a monster from the game database."""
        player = self.session.player
        if variable not in player.game_variables:
            logger.error(f"Game variable {variable} not found")
            return None
        monster_id = uuid.UUID(player.game_variables[variable])
        return get_monster_by_iid(self.session, monster_id)
