# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class InfoAction(EventAction):
    """
    Records monster's attribute values inside a game variable.
    It allows recording the monster's owner attribute values too.

    Script usage:

        .. code-block:: text

           info <variable>,<attribute>

    Script parameters:

        variable:
            Name of the variable where to store the monster id.

        attribute:
            The attribute to check (level, speed, etc.)

    Examples:

        "info name_variable,level"
        -> if the monster is lv 4, then it'll create a variable called:
        "info_level:4"

        "info name_variable,owner_steps"
        -> if the owner walked 69 steps, then it'll create a variable called:
        "info_owner_steps:69"
    """

    name = "info"
    variable: str
    attribute: str

    def start(self, session: Session) -> None:
        player = session.player
        attribute = self.attribute
        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID
        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            monster = player.monster_boxes.get_monsters_by_iid(monster_id)
            if monster is None:
                logger.error("Monster not found")
                self.stop()
                return

        character = session.client.get_monster_owner(monster)
        if character is None:
            logger.error(f"{monster.name}'s owner not found")
            self.stop()
            return

        attr = None
        if attribute.startswith("owner_"):
            _attr = attribute.replace("owner_", "")
            attr = getattr(character, _attr)
        else:
            attr = getattr(monster, attribute)

        client = session.client.event_engine
        var = f"{self.name}_{attribute}:{attr}"
        client.execute_action("set_variable", [var], True)
