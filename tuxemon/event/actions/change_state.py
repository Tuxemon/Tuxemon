# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
        # Don't override previous state if we are still in the state.
        client = self.session.client
        if client.current_state is None:
            # obligatory "should not happen"
            raise RuntimeError
        if client.current_state.name != self.state_name:
            if self.state_name == "JournalInfoState" and self.optional:
                journal = db.lookup(self.optional, table="monster")
                params1 = {"monster": journal}
                client.push_state(self.state_name, kwargs=params1)
            elif self.state_name == "MonsterInfoState" and self.optional:
                monster = self.retrieve_monster(self.optional)
                if monster is None:
                    logger.error("Monster not found")
                    return
                params2 = {"monster": monster, "source": self.name}
                client.push_state(self.state_name, kwargs=params2)
            elif self.state_name == "CharacterState" and self.optional:
                character = get_npc(self.session, self.optional)
                if character is None:
                    logger.error(f"{self.optional} not found")
                    return
                params3 = {"character": character}
                client.push_state(self.state_name, kwargs=params3)
            else:
                client.push_state(self.state_name)

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(self.state_name)
        except ValueError:
            self.stop()

    def retrieve_monster(self, variable: str) -> Optional[Monster]:
        player = self.session.player
        if variable not in player.game_variables:
            logger.error(f"Game variable {variable} not found")
            return None
        monster_id = uuid.UUID(player.game_variables[variable])
        return get_monster_by_iid(self.session, monster_id)
