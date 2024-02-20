# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class InfoAction(EventAction):
    """
    Records monster's attribute values inside a game variable.
    It allows to record the monster's owner attribute values too.

    Script usage:
        .. code-block::

            info <variable>,<attribute>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        attribute: The attribute to check (level, speed, etc.)

    eg. "info name_variable,level"
    -> if the monster is lv 4, then it'll create a variable called:
        "info_level:4"
    eg. "info name_variable,owner_steps"
    -> if the owner walked 69 steps, then it'll create a variable called:
        "info_owner_steps:69"

    """

    name = "info"
    variable: str
    attribute: str

    def start(self) -> None:
        player = self.session.player
        attribute = self.attribute
        variable = self.variable
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {variable} not found")
            return
        monster_id = uuid.UUID(player.game_variables[variable])
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return
        character = monster.owner
        if character is None:
            logger.error(f"{monster.name}'s owner not found!")
            return

        attr = None
        if attribute.startswith("owner_"):
            _attr = attribute.replace("owner_", "")
            attr = getattr(character, _attr)
        else:
            attr = getattr(monster, attribute)

        client = self.session.client.event_engine
        var = f"{self.name}_{attribute}:{attr}"
        client.execute_action("set_variable", [var], True)
